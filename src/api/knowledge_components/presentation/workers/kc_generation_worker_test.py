"""O worker da geração de KCs: trava como primeiro ato, estados do job e "nada parcial é gravado".

Roda `run_kc_generation(conn, assignment_id, job_id, llm=...)` sobre `tmp_db` + `data_root`
herméticos, com um LLM falso injetado: nenhum `claude` real, nenhuma cota gasta. Pina as transições
do job (pending → running → done), a trava pega no corpo e liberada ao sair, e a falha dura de
conteúdo: o job vira failed e não sobra KC nem Q-matrix parcial. Os testes pinam ESTADO.
"""

from __future__ import annotations

import os

import pandas as pd

from api.assignments.domain.entities.assignment_entity import Assignment
from api.assignments.domain.entities.classroom_entity import Classroom
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.knowledge_components.domain.entities.kc_generation_job_entity import (
    KnowledgeComponentGenerationJob,
)
from api.knowledge_components.infrastructure.repositories.sqlite_kc_generation_job_repository import (
    SqliteKnowledgeComponentGenerationJobRepository,
)
from api.knowledge_components.presentation.workers import kc_generation_worker
from api.knowledge_components.presentation.workers.kc_generation_worker import run_kc_generation
from api.shared.domain.value_objects.job_status import JobStatus
from api.shared.infrastructure import settings


class _FakeLLM:
    """LLMClient falso: devolve o que `respond()` mandar, sem tocar o `claude`."""

    def __init__(self, respond) -> None:
        self._respond = respond

    def generate(self, system: str, prompt: str, schema: dict) -> dict:
        return self._respond()


def _llm_ok() -> _FakeLLM:
    return _FakeLLM(lambda: {"kcs": [{"name": "laços", "reasoning": "usa for"}]})


def _jobs(conn) -> SqliteKnowledgeComponentGenerationJobRepository:
    return SqliteKnowledgeComponentGenerationJobRepository(conn)


ASSIGNMENT_ID = 439

_JAVA_BODIES = [
    "public int g0(int a, int b) { int s = a + b; return s; }",
    "public boolean g1(int n) { if (n > 0) { return true; } return false; }",
    "public int g2(int n) { while (n > 0) { n = n - 1; } return n; }",
]


def _row(subject, problem, ts, score, code, snapshot_id):
    return {
        "student_id": subject,
        "progsnap_assignment_id": ASSIGNMENT_ID,
        "problem_id": problem,
        "code_snapshot_id": snapshot_id,
        "code": code,
        "score": score,
        "submitted_at": ts,
        "event_type": "Run.Program",
        "is_correct": int(score == 1.0),
    }


def _canonical_df() -> pd.DataFrame:
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for s, body in enumerate(_JAVA_BODIES):
        for step, (pid, score) in enumerate([(1, 1.0), (2, 1.0), (3, 1.0)]):
            ts = base + pd.Timedelta(hours=s) + pd.Timedelta(minutes=step)
            rows.append(_row(f"S{s}", pid, ts, score, body, f"c{s}_{step}"))
    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")
    return df


def _seed_kc_ready(conn, data_root) -> tuple[int, int]:
    """turma + assignment trainable + Parquet canônico + kc_job pending. Devolve (aid, job)."""
    created = "2026-06-21T00:00:00Z"
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
            status="ready_for_kc_generation",
        )
    )
    clean_dir = data_root / "turma-x" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    _canonical_df().to_parquet(
        clean_dir / f"assignment_{ASSIGNMENT_ID}.parquet", engine="pyarrow", index=False
    )
    job_id = _jobs(conn).add(
        KnowledgeComponentGenerationJob(
            id=None, assignment_id=assignment_id, status=JobStatus.PENDING, created_at=created
        )
    )
    return assignment_id, job_id


def _holder_pid(conn):
    return conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()["holder_pid"]




def test_lock_busy_marks_failed_and_does_not_persist(tmp_db, data_root):
    # Dono vivo (este processo) segura o lock → a aquisição da CLI é negada.
    conn = tmp_db
    assignment_id, job_id = _seed_kc_ready(conn, data_root)
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='kc_gen', job_id=99 WHERE id=1;",
        (os.getpid(),),
    )

    run_kc_generation(conn, assignment_id, job_id, llm=_llm_ok())

    job = _jobs(conn).get(job_id)
    assert job.status == "failed"
    assert "busy" in (job.error_message or "").lower()
    assert _holder_pid(conn) == os.getpid()  # lock segue do dono vivo


def test_content_hard_fail_marks_failed_nothing_persisted(tmp_db, data_root):
    # O LLM devolve 0 KCs → após N tentativas o job inteiro marca failed e NADA é
    # persistido (nem kc, nem qmatrix, nem flip de status do assignment).
    conn = tmp_db
    assignment_id, job_id = _seed_kc_ready(conn, data_root)

    llm = _FakeLLM(lambda: {"kcs": []})

    run_kc_generation(conn, assignment_id, job_id, llm=llm)

    job = _jobs(conn).get(job_id)
    assert job.status == "failed"
    # Nada persistido.
    assert conn.execute("SELECT COUNT(*) FROM kc;").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM qmatrix;").fetchone()[0] == 0
    asg = SqliteAssignmentRepository(conn).get(assignment_id)
    assert asg.status == "ready_for_kc_generation"  # não avançou para kc_draft
    assert _holder_pid(conn) is None  # lock liberado mesmo na falha (with lock)


def test_small_dataset_skips_clustering_no_crash(tmp_db, data_root):
    # 2..10 nomes únicos de KC — abaixo do menor candidato {10,12,15}. O caminho real
    # é NÃO clusterizar (cada nome único = seu próprio cluster), sem tocar SBERT/silhouette.
    # Antes do fix: choose_kc_group_count estourava ValueError em max() de dict vazio → job failed.
    conn = tmp_db
    assignment_id, job_id = _seed_kc_ready(conn, data_root)

    # 3 problemas, cada um com um nome de KC DISTINTO → 3 nomes únicos (2 <= n_unique < 10).
    names = iter(["laços", "condicionais", "aritmética"])

    llm = _FakeLLM(lambda: {"kcs": [{"name": next(names), "reasoning": "x"}]})

    run_kc_generation(conn, assignment_id, job_id, llm=llm)

    job = _jobs(conn).get(job_id)
    assert job.status == "done"  # não falhou (sem crash de clustering)
    asg = SqliteAssignmentRepository(conn).get(assignment_id)
    assert asg.status == "kc_draft"
    # 3 nomes únicos → 3 KCs (um cluster por nome, sem labeling LLM).
    assert conn.execute("SELECT COUNT(*) FROM kc;").fetchone()[0] == 3
    assert _holder_pid(conn) is None


def test_mark_done_failure_is_atomic_with_persist(tmp_db, data_root, monkeypatch):
    # Se mark_done falhar, a flip para kc_draft NÃO pode persistir sozinha. Com mark_done
    # DENTRO da txn, o raise dá ROLLBACK do flip também → assignment segue 'trainable', job 'failed'
    # (estado consistente). Antes do fix: assignment 'kc_draft' + job 'failed' (inconsistente).
    conn = tmp_db
    assignment_id, job_id = _seed_kc_ready(conn, data_root)
    llm = _llm_ok()

    def _boom(self, *_a, **_k):
        raise RuntimeError("sqlite busy on mark_done")

    monkeypatch.setattr(SqliteKnowledgeComponentGenerationJobRepository, "mark_done", _boom)

    run_kc_generation(conn, assignment_id, job_id, llm=llm)

    asg = SqliteAssignmentRepository(conn).get(assignment_id)
    job = _jobs(conn).get(job_id)
    # Sem inconsistência: ou tudo persiste com job done, ou nada (aqui: rollback → trainable+failed).
    assert not (asg.status == "kc_draft" and job.status == "failed")
    assert asg.status == "ready_for_kc_generation"
    assert conn.execute("SELECT COUNT(*) FROM kc;").fetchone()[0] == 0
    assert _holder_pid(conn) is None


def test_success_transitions_job_and_acquires_lock(tmp_db, data_root):
    # Caminho feliz: lock adquirido como 1º ato, job pending→running→done, status vira kc_draft,
    # lock liberado ao sair. LLM mockado (nunca chama `claude`).
    conn = tmp_db
    assignment_id, job_id = _seed_kc_ready(conn, data_root)
    llm = _llm_ok()

    run_kc_generation(conn, assignment_id, job_id, llm=llm)

    job = _jobs(conn).get(job_id)
    assert job.status == "done"
    assert job.started_at is not None  # mark_running aconteceu
    asg = SqliteAssignmentRepository(conn).get(assignment_id)
    assert asg.status == "kc_draft"  # pipeline conclui em kc_draft
    assert conn.execute("SELECT COUNT(*) FROM kc;").fetchone()[0] >= 1  # KCs persistidos
    assert _holder_pid(conn) is None  # release garantido


def test_main_resolves_paths_from_env_and_runs_pipeline(tmp_path, monkeypatch):
    # O entrypoint do subprocess (`python -m api.knowledge_components.presentation.workers.kc_generation_worker`) nunca era exercitado: os
    # testes acima chamam o runner direto. Um erro em main() mata o processo antes de marcar o
    # job, e o kc_job fica 'pending' para sempre — sem nenhum teste falhar.
    kc_main = kc_generation_worker
    from api.shared.infrastructure.database.migrations.runner import run_migrations
    from api.shared.infrastructure.database.sqlite_connection import connect

    db_path = tmp_path / "app.db"
    run_migrations(connect(str(db_path)))
    # setattr antes de main() mutar os globais: o teardown do monkeypatch os restaura.
    monkeypatch.setattr(settings, "DB_PATH", "app.db")
    monkeypatch.setattr(settings, "DATA_ROOT", settings.DATA_ROOT)
    monkeypatch.setenv("EDMKT_DB_PATH", str(db_path))
    monkeypatch.setenv("EDMKT_DATA_ROOT", str(tmp_path / "data"))

    calls = []
    monkeypatch.setattr(
        kc_main,
        "run_kc_generation",
        lambda conn, assignment_id, job_id: calls.append((assignment_id, job_id)) or {},
    )

    exit_code = kc_main.main(["--assignment", "7", "--job-id", "3"])

    assert exit_code == 0
    assert calls == [(7, 3)]
    assert settings.DB_PATH == str(db_path)
    assert settings.DATA_ROOT == tmp_path / "data"
