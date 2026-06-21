"""CLI de treino headless `_run_training` — orquestração MODEL-01/02/03 (plano 04-03).

Cobre os 6 estados testáveis da orquestração sem disparar o `subprocess.Popen` real
(testado à parte no plano 04-04): chama `_run_training(conn, assignment_id, job_id)`
direto, CPU + épocas reduzidas, sobre `tmp_db` + `data_root` herméticos. O Parquet
canônico da Fase 3 é montado em `data/<slug>/clean/assignment_<aid>.parquet` (a mesma
forma que `service._persist_atomic` grava) e o lock é asseverado por `holder_pid` no
estilo de test_lock/test_ingestion_service. NUNCA o CSEDM real; nenhum AUC mágico —
as asserções pinam transições de estado (status, job, holder_pid), não numerics.
"""

from __future__ import annotations

import os

import pandas as pd
import pytest
import torch

from edmkt_app import train
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos

ASSIGNMENT_ID = 439

# Oito corpos de método estruturalmente distintos (espelha test_pipeline.progsnap_df):
# garante OOV>0 no held-out e cache com paths reais para um treino end-to-end em CPU.
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

# Arquitetura congelada; só as épocas caem para um smoke CPU rápido (nunca no FROZEN_CONFIG).
_FAST_EPOCHS = 3


def _row(subject, problem, ts, score, code, csid):
    correct = int(score == 1.0)
    return {
        "SubjectID": subject,
        "AssignmentID": ASSIGNMENT_ID,
        "ProblemID": problem,
        "CodeStateID": csid,
        "Code": code,
        "Score": score,
        "ServerTimestamp": ts,
        "EventType": "Run.Program",
        "correct": correct,
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
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")
    return df


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    """Aponta train.DATA_ROOT e features_cache.DATA_ROOT para tmp_path — FS hermético."""
    from edmkt_app import features_cache

    monkeypatch.setattr(train, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(features_cache, "DATA_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def fast_config(monkeypatch):
    """Reduz épocas via FROZEN_CONFIG visto pela CLI, sem mutar o MappingProxyType global."""
    from edmkt_core.config import FROZEN_CONFIG

    fast = {**FROZEN_CONFIG, "epochs": _FAST_EPOCHS}
    monkeypatch.setattr(train, "FROZEN_CONFIG", fast)
    return fast


def _seed_trainable(conn, data_root) -> tuple[int, int]:
    """Monta turma + assignment trainable + Parquet canônico + job pending. Devolve (aid, job)."""
    created = "2019-03-01T00:00:00+00:00"
    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name="Turma X", created_at=created)
    )
    assignment_id = repos.AssignmentRepository(conn).insert(
        models.Assignment(
            id=None,
            turma_id=turma_id,
            name=f"Assignment {ASSIGNMENT_ID}",
            current_version_id=None,
            created_at=created,
            status="trainable",
        )
    )
    clean_dir = data_root / "turma-x" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    _canonical_df().to_parquet(
        clean_dir / f"assignment_{ASSIGNMENT_ID}.parquet", engine="pyarrow", index=False
    )
    job_id = repos.TrainingJobRepository(conn).insert(
        models.TrainingJob(id=None, assignment_id=assignment_id, status="pending", created_at=created)
    )
    return assignment_id, job_id


def _holder_pid(conn):
    return conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()["holder_pid"]


def _dead_pid() -> int:
    # PID com altíssima probabilidade de não existir (espelha test_lock._dead_pid).
    return 2**22


# --- caso 1: end-to-end trainable -> trained + artefato + job done (MODEL-01, critério 4) ---


def test_end_to_end_trains_persists_and_flips_status(tmp_db, data_root, fast_config):
    conn = tmp_db
    assignment_id, job_id = _seed_trainable(conn, data_root)

    train._run_training(conn, assignment_id, job_id)

    asg = repos.AssignmentRepository(conn).get(assignment_id)
    assert asg.status == "trained"
    assert asg.current_version_id is not None
    artifact = repos.ModelArtifactRepository(conn).get(asg.current_version_id)
    assert artifact is not None and artifact.assignment_id == assignment_id
    job = repos.TrainingJobRepository(conn).get(job_id)
    assert job.status == "done"
    assert _holder_pid(conn) is None  # release garantido ao sair do `with lock`


# --- caso 2: lock por PID vivo -> job failed "pipeline busy", sem treino (D-02, MODEL-03) ---


def test_lock_busy_marks_failed_and_does_not_train(tmp_db, data_root, fast_config):
    conn = tmp_db
    assignment_id, job_id = _seed_trainable(conn, data_root)
    # Dono vivo (este processo) segura o lock — a aquisição da CLI deve ser negada.
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='training', job_id=99 WHERE id=1;",
        (os.getpid(),),
    )

    train._run_training(conn, assignment_id, job_id)

    job = repos.TrainingJobRepository(conn).get(job_id)
    assert job.status == "failed"
    assert "busy" in (job.error_message or "").lower()
    asg = repos.AssignmentRepository(conn).get(assignment_id)
    assert asg.status == "trainable"  # não treinou
    assert asg.current_version_id is None
    assert _holder_pid(conn) == os.getpid()  # o lock segue do dono vivo


# --- caso 3: on_epoch grava current_epoch + train_loss no TrainingJob (MODEL-02, D-05/D-06) ---


def test_epoch_callback_writes_progress(tmp_db, data_root, fast_config):
    conn = tmp_db
    assignment_id, job_id = _seed_trainable(conn, data_root)

    train._run_training(conn, assignment_id, job_id)

    job = repos.TrainingJobRepository(conn).get(job_id)
    assert job.current_epoch == _FAST_EPOCHS  # avançou até a última época
    assert job.total_epochs == _FAST_EPOCHS
    assert job.train_loss is not None
    assert job.started_at is not None


# --- caso 4: train_and_evaluate levanta -> assignment trainable, job failed, lock liberado ---


def test_training_failure_releases_lock_and_keeps_trainable(tmp_db, data_root, fast_config, monkeypatch):
    conn = tmp_db
    assignment_id, job_id = _seed_trainable(conn, data_root)

    def _boom(*args, **kwargs):
        raise RuntimeError("treino explodiu")

    monkeypatch.setattr(train, "train_and_evaluate", _boom)

    train._run_training(conn, assignment_id, job_id)

    job = repos.TrainingJobRepository(conn).get(job_id)
    assert job.status == "failed"
    assert "explodiu" in (job.error_message or "")
    asg = repos.AssignmentRepository(conn).get(assignment_id)
    assert asg.status == "trainable"
    assert asg.current_version_id is None
    assert _holder_pid(conn) is None  # liberado mesmo sob exceção (SC3)


# --- caso 5: CUDA OOM -> job failed com mensagem de VRAM, lock liberado (D-11, Pitfall 4) ---


def test_cuda_oom_fails_gracefully(tmp_db, data_root, fast_config, monkeypatch):
    conn = tmp_db
    assignment_id, job_id = _seed_trainable(conn, data_root)

    def _oom(*args, **kwargs):
        raise torch.cuda.OutOfMemoryError("CUDA out of memory")

    monkeypatch.setattr(train, "train_and_evaluate", _oom)

    train._run_training(conn, assignment_id, job_id)

    job = repos.TrainingJobRepository(conn).get(job_id)
    assert job.status == "failed"
    assert "VRAM" in (job.error_message or "")
    asg = repos.AssignmentRepository(conn).get(assignment_id)
    assert asg.status == "trainable"
    assert _holder_pid(conn) is None


# --- caso 6: taxa de parse 3-vias recordada/recuperável (D-09 consumer, critério 3) ---


def test_parse_rate_is_recorded(tmp_db, data_root, fast_config):
    conn = tmp_db
    assignment_id, job_id = _seed_trainable(conn, data_root)

    result = train._run_training(conn, assignment_id, job_id)

    assert result is not None
    assert "parse_rate" in result
    # Todos os snapshots do fixture parseiam e têm paths ⇒ taxa = 1.0.
    assert result["parse_rate"] == pytest.approx(1.0)
