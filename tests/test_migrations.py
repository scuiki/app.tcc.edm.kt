"""Tests for the SQLite connection + migration runner (D-02, MODEL-03/MODEL-04 foundation).

Pins the persistence foundation the rest of Phase 2 stands on: the connection PRAGMAs
(foreign_keys=ON — OFF by default in SQLite — and WAL), the forward-only runner over
PRAGMA user_version (ordered, idempotent, atomic bump), and the 0001 schema (8 domain
entities + the single pipeline_lock row). Hermetic and CPU-only — no GPU, no real CSEDM.
"""

from __future__ import annotations

import sqlite3

from edmkt_app.persistence import connect, run_migrations
from edmkt_app.persistence.migrations import runner as runner_mod

# The 8 domain entities (D-01) plus the dedicated one-row lock table.
_DOMAIN_TABLES = {
    "turma",
    "assignment",
    "submission",
    "kc",
    "qmatrix",
    "model_artifact",
    "mastery_prediction",
    "training_job",
}
_ALL_TABLES = _DOMAIN_TABLES | {"pipeline_lock"}


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    ).fetchall()
    return {r["name"] for r in rows}


def _user_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version;").fetchone()[0]


# Última versão de schema aplicada pelo runner (sobe a cada degrau NNNN_*.sql novo).
_LATEST_VERSION = 4

# As 6 colunas de progresso por-época que 0003 adiciona ao training_job (D-06).
_TRAINING_JOB_PROGRESS_COLUMNS = {
    "current_epoch",
    "total_epochs",
    "train_loss",
    "started_at",
    "updated_at",
    "error_message",
}


def test_runner_applies_in_order(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    assert _user_version(conn) == 0
    run_migrations(conn)
    assert _user_version(conn) == _LATEST_VERSION
    assert _ALL_TABLES <= _table_names(conn)


def test_runner_idempotent(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    # Second pass must not re-execute the DDL ("table already exists") nor bump again.
    run_migrations(conn)
    assert _user_version(conn) == _LATEST_VERSION


def test_runner_bumps_atomically(tmp_path):
    """A synthetic invalid step must ROLLBACK — user_version never advances past the
    last good step (DDL + bump share one transaction, D-02)."""
    migrations_dir = tmp_path / "migs"
    migrations_dir.mkdir()
    # A deliberately broken DDL step: parses past the first statement then fails.
    (migrations_dir / "0001_broken.sql").write_text(
        "CREATE TABLE ok (id INTEGER PRIMARY KEY);\n"
        "CREATE TABLE bad (id INTEGER PRIMARY KEY, FOREIGN KEY (id) REFERENCES nonexistent(x));\n"
        "THIS IS NOT VALID SQL;\n"
    )
    conn = connect(str(tmp_path / "app.db"))
    try:
        run_migrations(conn, migrations_dir=migrations_dir)
    except sqlite3.Error:
        pass
    else:
        raise AssertionError("expected the broken migration to raise")
    # The bump must NOT have happened — the whole step rolled back.
    assert _user_version(conn) == 0
    assert "ok" not in _table_names(conn)


def test_connection_pragmas(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    assert conn.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
    assert conn.execute("PRAGMA journal_mode;").fetchone()[0].lower() == "wal"


def test_pipeline_lock_seeded(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    rows = conn.execute("SELECT id, holder_pid FROM pipeline_lock;").fetchall()
    assert len(rows) == 1
    assert rows[0]["id"] == 1
    assert rows[0]["holder_pid"] is None


def test_inline_comment_does_not_break_split(tmp_path):
    """Um statement com `-- comentário` inline aplica sem OperationalError mesmo quando o
    comentário contém um `;` (que, sem strip do comentário, racha o split e gruda um
    fragmento inválido no próximo statement); e `--` dentro de string literal NÃO é
    truncado (WR-02)."""
    migrations_dir = tmp_path / "migs"
    migrations_dir.mkdir()
    (migrations_dir / "0001_inline_comments.sql").write_text(
        # o `;` dentro do comentário inline é o gatilho real do bug do split.
        "CREATE TABLE foo (id INTEGER PRIMARY KEY, label TEXT);  -- nota; com ponto-e-vírgula\n"
        "INSERT INTO foo (id, label) VALUES (1, 'a--b');  -- o -- na string não pode sumir\n"
        "SELECT 1;\n"
    )
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn, migrations_dir=migrations_dir)

    assert _user_version(conn) == 1
    assert "foo" in _table_names(conn)
    # `--` dentro da string literal foi preservado (não truncado pelo strip de comentário).
    row = conn.execute("SELECT label FROM foo WHERE id=1;").fetchone()
    assert row["label"] == "a--b"


def test_default_migrations_dir_is_package_local(tmp_path):
    """run_migrations() with no dir argument resolves the package's own migrations/."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)  # uses the default dir
    assert _user_version(conn) == _LATEST_VERSION
    # The default dir is the package's migrations folder (sanity on the resolution).
    assert runner_mod._default_migrations_dir().name == "migrations"


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table});")}


def test_migration_0002_grows_assignment_and_submission(tmp_path):
    """0002 é forward-only: aplica sobre o 0001, bumpa user_version=2 e adiciona as colunas
    de estado do assignment (status) + event_type do stream canônico na submission (D-05/D-13)."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 2
    assert "status" in _column_names(conn, "assignment")
    assert "event_type" in _column_names(conn, "submission")


def test_migration_0003_grows_training_job_progress(tmp_path):
    """0003 é forward-only: bumpa user_version=3 e adiciona as 6 colunas de progresso
    por-época do training_job (D-06) — o que a CLI da plan 03 escreve durante o treino."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 3
    assert _TRAINING_JOB_PROGRESS_COLUMNS <= _column_names(conn, "training_job")


def test_migration_0004_adds_parse_rate(tmp_path):
    """0004 é forward-only: bumpa user_version=4 e adiciona a coluna parse_rate ao
    training_job (D-06 estendido/MODEL-05) — a taxa de parse que o subprocess grava p/ o SC-3."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) == 4
    assert "parse_rate" in _column_names(conn, "training_job")


def test_migration_0004_repo_round_trips_parse_rate(tmp_path):
    """Grava parse_rate via o repo e relê via get() — prova o caminho de persistência."""
    from edmkt_app.persistence import repositories

    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    repo = repositories.TrainingJobRepository(conn)
    job_id = _seed_training_job(conn)

    repo.mark_done(job_id, updated_at="2026-01-01T00:10:00Z", parse_rate=0.86)
    job = repo.get(job_id)
    assert job.parse_rate == 0.86


def _seed_training_job(conn: sqlite3.Connection) -> int:
    """turma → assignment → training_job; devolve o job_id (FK exige a cadeia)."""
    from edmkt_app.persistence import models, repositories

    turma_id = repositories.TurmaRepository(conn).insert(
        models.Turma(id=None, name="t", created_at="2026-01-01T00:00:00Z")
    )
    assignment_id = repositories.AssignmentRepository(conn).insert(
        models.Assignment(
            id=None,
            turma_id=turma_id,
            name="a",
            current_version_id=None,
            created_at="2026-01-01T00:00:00Z",
        )
    )
    return repositories.TrainingJobRepository(conn).insert(
        models.TrainingJob(
            id=None, assignment_id=assignment_id, status="queued", created_at="2026-01-01T00:00:00Z"
        )
    )


def test_training_job_born_null_progress(tmp_path):
    """Uma linha criada antes de qualquer escrita de progresso lê as 6 colunas novas como
    None (nascem NULL nas linhas pré-progresso)."""
    from edmkt_app.persistence import repositories

    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    job_id = _seed_training_job(conn)

    job = repositories.TrainingJobRepository(conn).get(job_id)
    assert job is not None
    assert job.current_epoch is None
    assert job.total_epochs is None
    assert job.train_loss is None
    assert job.started_at is None
    assert job.updated_at is None
    assert job.error_message is None


def test_training_job_update_progress_roundtrip(tmp_path):
    from edmkt_app.persistence import repositories

    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    repo = repositories.TrainingJobRepository(conn)
    job_id = _seed_training_job(conn)

    repo.update_progress(job_id, current_epoch=5, train_loss=0.42, updated_at="2026-01-01T00:05:00Z")
    job = repo.get(job_id)
    assert job.current_epoch == 5
    assert job.train_loss == 0.42
    assert job.updated_at == "2026-01-01T00:05:00Z"


def test_training_job_mark_transitions(tmp_path):
    from edmkt_app.persistence import repositories

    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    repo = repositories.TrainingJobRepository(conn)
    job_id = _seed_training_job(conn)

    repo.mark_running(job_id, total_epochs=40, started_at="2026-01-01T00:00:01Z")
    job = repo.get(job_id)
    assert job.status == "running"
    assert job.total_epochs == 40
    assert job.started_at == "2026-01-01T00:00:01Z"

    repo.mark_done(job_id, updated_at="2026-01-01T00:10:00Z")
    job = repo.get(job_id)
    assert job.status == "done"
    assert job.updated_at == "2026-01-01T00:10:00Z"

    repo.mark_failed(job_id, "boom")
    job = repo.get(job_id)
    assert job.status == "failed"
    assert job.error_message == "boom"


def test_pyarrow_parquet_roundtrip(tmp_path):
    """Guarda de regressão do checkpoint manual do Task 1: o engine pyarrow do to_parquet
    está instalado e faz round-trip no container (sem ele a ingestão D-13 falha)."""
    import pandas as pd

    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    path = tmp_path / "t.parquet"
    df.to_parquet(path, engine="pyarrow", index=False)
    back = pd.read_parquet(path)
    assert back.equals(df)
