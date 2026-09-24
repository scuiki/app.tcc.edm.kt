# O worker de treino, estados do job, trava, curva de loss, taxa de parse e o recorte Run.Program.

from __future__ import annotations

import os

import pandas as pd
import pytest
import torch

from api.assignments.domain.entities.assignment_entity import Assignment
from api.classrooms.domain.entities.classroom_entity import Classroom
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.classrooms.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.classroom_import.infrastructure.repositories.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)
from api.model_training.domain.entities.training_job_entity import TrainingJob
from api.model_training.infrastructure.implementations.ml_code_dkt_trainer import MlCodeDktTrainer
from api.model_training.infrastructure.repositories.sqlite_trained_model_repository import (
    SqliteTrainedModelRepository,
)
from api.model_training.infrastructure.repositories.sqlite_training_epoch_metric_repository import (
    SqliteTrainingEpochMetricRepository,
)
from api.model_training.infrastructure.repositories.sqlite_training_job_repository import (
    SqliteTrainingJobRepository,
)
from api.model_training.presentation.workers.training_worker import run_training
from api.shared.domain.value_objects.job_status import JobStatus
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS
from tests.fixtures.job_lock import lock_holder_pid
from tests.fixtures.problems import add_problems

ASSIGNMENT_ID = 439

# Oito corpos de método distintos (espelha test_pipeline.progsnap_df), garantindo OOV>0 no held-out.
_JAVA_BODIES = [
    "public int g0(int a, int b) { int s = a + b; return s; }",
    "public int g1(int a) { for (int i = 0; i < a; i++) { a = a * 2; } return a; }",
    "public boolean g2(int n) { if (n > 0) { return true; } return false; }",
    "public int g3(int n) { while (n > 0) { n = n - 1; } return n; }",
    "public int g4(int[] xs) { int t = 0; for (int x : xs) { t += x; } return t; }",
    'public String g5(boolean b) { return b ? "yes" : "no"; }',
    "public int g6(int n) { switch (n) { case 0: return 1; default: return n; } }",
    "public int g7(int n) { try { return 10 / n; } catch (Exception e) { return -1; } }",
]

# Arquitetura congelada; só as épocas caem, para um smoke CPU rápido (nunca no real).
_FAST_EPOCHS = 3


def _row(subject, problem, ts, score, code, snapshot_id):
    correct = int(score == 1.0)
    return {
        "student_id": subject,
        "progsnap_assignment_id": ASSIGNMENT_ID,
        "problem_id": problem,
        "code_snapshot_id": snapshot_id,
        "code": code,
        "score": score,
        "submitted_at": ts,
        "event_type": "Run.Program",
        "is_correct": correct,
    }


def _canonical_df() -> pd.DataFrame:
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for s in range(8):
        body = _JAVA_BODIES[s]
        plan = [(1, 0.0), (2, 1.0), (1, 1.0), (3, 0.0), (2, 1.0)]
        for step, (pid, score) in enumerate(plan):
            ts = base + pd.Timedelta(hours=s) + pd.Timedelta(minutes=step)
            rows.append(_row(f"S{s}", pid, ts, score, body, f"c{s}_{step}"))
    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")
    return df


_FAST_HYPERPARAMETERS = {**CODE_DKT_HYPERPARAMETERS, "epochs": _FAST_EPOCHS}


@pytest.fixture
def fast_trainer() -> MlCodeDktTrainer:
    # O treinador real com poucas épocas (os hiperparâmetros congelados não são mutados).
    return MlCodeDktTrainer(hyperparameters=_FAST_HYPERPARAMETERS)


def _failing_trainer(error: Exception) -> MlCodeDktTrainer:
    def _raise(*args, **kwargs):
        raise error

    return MlCodeDktTrainer(hyperparameters=_FAST_HYPERPARAMETERS, train=_raise)


def _canonical_df_with_compile_errors() -> pd.DataFrame:
    # Stream realista, Run.Program parseável + Compile.Error com Java quebrado (57,6% no A439 real).
    df = _canonical_df()
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    broken = []
    for s in range(8):
        for step in range(3):
            ts = base + pd.Timedelta(hours=s) + pd.Timedelta(minutes=30 + step)
            row = _row(f"S{s}", 1, ts, 0.0, "public int oops( { return ;;; }", f"e{s}_{step}")
            row["event_type"] = "Compile.Error"
            row["is_correct"] = 0  # correct exige Run.Program e Score == 1.0
            broken.append(row)
    out = pd.concat([df, pd.DataFrame(broken)], ignore_index=True)
    out["submitted_at"] = pd.to_datetime(out["submitted_at"], utc=True)
    out["progsnap_assignment_id"] = out["progsnap_assignment_id"].astype("Int64")
    out["problem_id"] = out["problem_id"].astype("Int64")
    return out.sort_values(["student_id", "submitted_at"]).reset_index(drop=True)


def _seed_approved(conn, data_root, df: pd.DataFrame | None = None) -> tuple[int, int]:
    # Turma + assignment com a Q-matrix aprovada + dado limpo + job pending. Devolve (aid, job).
    created = "2019-03-01T00:00:00+00:00"
    classroom_id = SqliteClassroomRepository(conn).add(
        Classroom(id=None, name="Turma X", created_at=created)
    )
    assignment_id = SqliteAssignmentRepository(conn).add(
        Assignment(
            id=None,
            classroom_id=classroom_id,
            name=f"Assignment {ASSIGNMENT_ID}",
            progsnap_assignment_id=ASSIGNMENT_ID,
            published_model_id=None,
            created_at=created,
            status="kc_approved",
        )
    )
    events = _canonical_df() if df is None else df
    add_problems(conn, assignment_id, events["problem_id"].dropna().unique())
    SqliteSubmissionRepository(conn).add_many(assignment_id, events)
    job_id = SqliteTrainingJobRepository(conn).add(
        TrainingJob(id=None, assignment_id=assignment_id, status=JobStatus.PENDING, created_at=created)
    )
    return assignment_id, job_id


def _dead_pid() -> int:
    # PID com altíssima probabilidade de não existir (espelha test_lock._dead_pid).
    return 2**22


# --- caso 1, de ponta a ponta, kc_approved -> trained + artefato + job done ---


def test_end_to_end_trains_persists_and_flips_status(tmp_db, data_root, fast_trainer):
    conn = tmp_db
    assignment_id, job_id = _seed_approved(conn, data_root)

    run_training(conn, assignment_id, job_id, trainer=fast_trainer)

    asg = SqliteAssignmentRepository(conn).get(assignment_id)
    assert asg.status == "trained"
    assert asg.published_model_id is not None
    artifact = SqliteTrainedModelRepository(conn).get(asg.published_model_id)
    assert artifact is not None and artifact.assignment_id == assignment_id
    job = SqliteTrainingJobRepository(conn).get(job_id)
    assert job.status == "done"
    assert lock_holder_pid(conn) is None  # release garantido ao sair do `with lock`


# --- caso 2, lock por PID vivo -> job failed "pipeline busy", sem treino ---


def test_lock_busy_marks_failed_and_does_not_train(tmp_db, data_root, fast_trainer):
    conn = tmp_db
    assignment_id, job_id = _seed_approved(conn, data_root)
    # Dono vivo (este processo) segura o lock; a aquisição da CLI deve ser negada.
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='training', job_id=99 WHERE id=1;",
        (os.getpid(),),
    )

    run_training(conn, assignment_id, job_id, trainer=fast_trainer)

    job = SqliteTrainingJobRepository(conn).get(job_id)
    assert job.status == "failed"
    assert "busy" in (job.error_message or "").lower()
    asg = SqliteAssignmentRepository(conn).get(assignment_id)
    assert asg.status == "kc_approved"  # não treinou
    assert asg.published_model_id is None
    assert lock_holder_pid(conn) == os.getpid()  # o lock segue do dono vivo


# --- caso 3, on_epoch grava current_epoch + train_loss no TrainingJob ---


def test_epoch_callback_writes_progress(tmp_db, data_root, fast_trainer):
    conn = tmp_db
    assignment_id, job_id = _seed_approved(conn, data_root)

    run_training(conn, assignment_id, job_id, trainer=fast_trainer)

    job = SqliteTrainingJobRepository(conn).get(job_id)
    assert job.total_epochs == _FAST_EPOCHS
    assert job.started_at is not None

    # A curva é append-only (migração 0008); antes sobrescrevia e só sobrava o último valor
    serie = SqliteTrainingEpochMetricRepository(conn).list_by_job(job_id)
    assert [m.epoch for m in serie] == list(range(1, _FAST_EPOCHS + 1))
    assert all(m.train_loss is not None for m in serie)


# --- caso 4, o treino levanta -> assignment segue kc_approved, job failed, lock liberado ---


def test_training_failure_releases_lock_and_keeps_kc_approved(tmp_db, data_root):
    conn = tmp_db
    assignment_id, job_id = _seed_approved(conn, data_root)

    run_training(conn, assignment_id, job_id, trainer=_failing_trainer(RuntimeError("treino explodiu")))

    job = SqliteTrainingJobRepository(conn).get(job_id)
    assert job.status == "failed"
    assert "explodiu" in (job.error_message or "")
    asg = SqliteAssignmentRepository(conn).get(assignment_id)
    assert asg.status == "kc_approved"
    assert asg.published_model_id is None
    assert lock_holder_pid(conn) is None  # liberado mesmo sob exceção


# --- caso 5, CUDA OOM -> job failed com mensagem de VRAM, lock liberado ---


def test_cuda_oom_fails_gracefully(tmp_db, data_root):
    conn = tmp_db
    assignment_id, job_id = _seed_approved(conn, data_root)

    run_training(
        conn,
        assignment_id,
        job_id,
        trainer=_failing_trainer(torch.cuda.OutOfMemoryError("CUDA out of memory")),
    )

    job = SqliteTrainingJobRepository(conn).get(job_id)
    assert job.status == "failed"
    assert "VRAM" in (job.error_message or "")
    asg = SqliteAssignmentRepository(conn).get(assignment_id)
    assert asg.status == "kc_approved"
    assert lock_holder_pid(conn) is None


# --- caso 6, taxa de parse 3-vias recordada/recuperável ---


def test_parse_rate_is_recorded(tmp_db, data_root, fast_trainer):
    conn = tmp_db
    assignment_id, job_id = _seed_approved(conn, data_root)

    result = run_training(conn, assignment_id, job_id, trainer=fast_trainer)

    assert result is not None
    assert "java_parse_rate" in result
    # Todos os snapshots do fixture parseiam e têm paths ⇒ taxa = 1.0.
    assert result["java_parse_rate"] == pytest.approx(1.0)


def test_parse_rate_is_persisted(tmp_db, data_root, fast_trainer):
    # A taxa não pode viver só no retorno (perdido no subprocess); sobrevive na linha do job
    conn = tmp_db
    assignment_id, job_id = _seed_approved(conn, data_root)

    run_training(conn, assignment_id, job_id, trainer=fast_trainer)

    job = SqliteTrainingJobRepository(conn).get(job_id)
    assert job is not None
    assert job.java_parse_rate == pytest.approx(1.0)


# --- caso 7, o stream de treino é só Run.Program (fidelidade a Shi et al. 2022) ---


def test_compile_errors_never_reach_the_training_stream(tmp_db, data_root, fast_trainer):
    # Compile.Error fica no limpo (estatísticas), mas nunca no treino (AUC caiu p/ 0,6959 no A439)
    conn = tmp_db
    assignment_id, job_id = _seed_approved(
        conn, data_root, df=_canonical_df_with_compile_errors()
    )

    result = run_training(conn, assignment_id, job_id, trainer=fast_trainer)

    assert result is not None
    assert result["java_parse_rate"] == pytest.approx(1.0)


def test_main_resolves_paths_from_env_and_runs_training(tmp_path, monkeypatch):
    # O entrypoint do subprocess, um erro em main() mataria o processo antes de marcar o job.
    from api.model_training.presentation.workers import training_worker
    from api.shared.infrastructure import settings
    from api.shared.infrastructure.database.migrations.runner import run_migrations
    from api.shared.infrastructure.database.sqlite_connection import connect

    db_path = tmp_path / "app.db"
    run_migrations(connect(str(db_path)))
    monkeypatch.setattr(settings, "DB_PATH", "app.db")
    monkeypatch.setattr(settings, "DATA_ROOT", settings.DATA_ROOT)
    monkeypatch.setenv("EDMKT_DB_PATH", str(db_path))
    monkeypatch.setenv("EDMKT_DATA_ROOT", str(tmp_path / "data"))
    calls = []
    monkeypatch.setattr(
        training_worker,
        "run_training",
        lambda conn, assignment_id, job_id: calls.append((assignment_id, job_id)) or {},
    )

    assert training_worker.main(["--assignment", "7", "--job-id", "3"]) == 0
    assert calls == [(7, 3)]
    assert settings.DATA_ROOT == tmp_path / "data"
