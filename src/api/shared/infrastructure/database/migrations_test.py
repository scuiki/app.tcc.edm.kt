"""Tests for the SQLite connection + migration runner (D-02, MODEL-03/MODEL-04 foundation).

Pins the persistence foundation the rest of Phase 2 stands on: the connection PRAGMAs
(foreign_keys=ON — OFF by default in SQLite — and WAL), the forward-only runner over
PRAGMA user_version (ordered, idempotent, atomic bump), and the 0001 schema (8 domain
entities + the single pipeline_lock row). Hermetic and CPU-only — no GPU, no real CSEDM.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from api.shared.infrastructure.database.migrations.runner import run_migrations
from api.shared.infrastructure.database.sqlite_connection import connect
from api.shared.infrastructure.database.migrations import runner as runner_mod

# The 8 domain entities (D-01) plus the dedicated one-row lock table.
_DOMAIN_TABLES = {
    "classroom",
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
# Derivada dos arquivos, não um literal: cada migration nova quebrava estes testes por
# envelhecimento, não por defeito.
_LATEST_VERSION = max(
    int(f.name[:4])
    for f in (Path(__file__).resolve().parent / "migrations").glob("[0-9][0-9][0-9][0-9]_*.sql")
)

# As colunas de progresso que sobrevivem de 0003 no training_job (D-06); current_epoch e
# train_loss saíram na 0009, o progresso por época vive em training_metric.
_TRAINING_JOB_PROGRESS_COLUMNS = {
    "total_epochs",
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
    """0003 é forward-only: bumpa user_version=3 e adiciona as colunas de progresso do
    training_job (D-06) que a CLI de treino escreve."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 3
    assert _TRAINING_JOB_PROGRESS_COLUMNS <= _column_names(conn, "training_job")


def test_migration_0004_adds_parse_rate(tmp_path):
    """0004 é forward-only: bumpa user_version>=4 e adiciona a coluna parse_rate ao
    training_job (D-06 estendido/MODEL-05) — a taxa de parse que o subprocess grava p/ o SC-3."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 4
    assert "parse_rate" in _column_names(conn, "training_job")


def test_migration_0005_adds_kc_index_and_kc_job(tmp_path):
    """0005 é forward-only: bumpa user_version=5, adiciona a coluna kc.kc_index (id de cluster
    0..N, fidelidade c/ artefatos TCC, D-06/Open Q2) e cria a tabela kc_job que espelha
    training_job (estado do pipeline KCGen-KT lido por polling GET, D-05/KC-01)."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 5
    assert "kc_index" in _column_names(conn, "kc")
    assert "kc_job" in _table_names(conn)
    # A tabela kc_job tem a forma do job de background (espelha training_job): status + estágio.
    assert {"id", "assignment_id", "status", "created_at", "stage", "error_message"} <= (
        _column_names(conn, "kc_job")
    )


def test_migration_0006_adds_qmatrix_unique_index(tmp_path):
    """0006 é forward-only: bumpa user_version=6 e cria o índice UNIQUE que torna o
    INSERT/UPDATE OR IGNORE de qmatrix real (WR-04)."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 6
    indexes = {
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='qmatrix';"
        )
    }
    assert "uq_qmatrix_assignment_kc_problem" in indexes


def test_migration_0007_adds_first_auc(tmp_path):
    """0007 é forward-only: adiciona o AUC do treino ao model_artifact (DASH-05/D-05); a 0009
    renomeia a coluna para first_attempt_auc."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= _LATEST_VERSION
    assert "first_attempt_auc" in _column_names(conn, "model_artifact")


def test_first_attempt_auc_is_nullable(tmp_path):
    """model_artifact.first_attempt_auc guarda o AUC do treino e nasce NULL quando não informado
    (os artefatos anteriores à 0007)."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    aid = _seed_assignment(conn)
    conn.execute(
        "INSERT INTO model_artifact (assignment_id, version_number, content_hash, artifact_dir, "
        "created_at, first_attempt_auc) VALUES (?, 1, 'h1', 'v1', 't0', 0.73), "
        "(?, 2, 'h2', 'v2', 't0', NULL);",
        (aid, aid),
    )
    rows = conn.execute(
        "SELECT version_number, first_attempt_auc FROM model_artifact ORDER BY version_number;"
    ).fetchall()
    assert [tuple(r) for r in rows] == [(1, 0.73), (2, None)]


def test_qmatrix_unique_blocks_duplicate_binding(tmp_path):
    """O trio (assignment_id, kc_id, problem_id) é único (0006): um INSERT do mesmo trio levanta
    IntegrityError, e é isso que torna real o INSERT OR IGNORE de quem grava vínculos."""
    import sqlite3 as _sqlite3

    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    aid = _seed_assignment(conn)
    kc_id = conn.execute(
        "INSERT INTO kc (assignment_id, name) VALUES (?, 'k');", (aid,)
    ).lastrowid
    insert = "INSERT INTO qmatrix (assignment_id, kc_id, problem_id) VALUES (?, ?, 7);"
    conn.execute(insert, (aid, kc_id))

    with pytest.raises(_sqlite3.IntegrityError):
        conn.execute(insert, (aid, kc_id))
    conn.execute(insert.replace("INSERT", "INSERT OR IGNORE"), (aid, kc_id))
    n = conn.execute("SELECT COUNT(*) FROM qmatrix;").fetchone()[0]
    assert n == 1


def test_training_job_parse_rate_round_trips(tmp_path):
    """training_job.parse_rate (0004) guarda a taxa de parse do javalang do treino."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    job_id = _seed_training_job(conn)

    conn.execute("UPDATE training_job SET parse_rate = 0.86 WHERE id = ?;", (job_id,))
    row = conn.execute("SELECT parse_rate FROM training_job WHERE id = ?;", (job_id,)).fetchone()
    assert row["parse_rate"] == 0.86


def _seed_assignment(conn: sqlite3.Connection) -> int:
    """classroom → assignment, em SQL puro (este teste é do schema, não de um repositório)."""
    classroom_id = conn.execute(
        "INSERT INTO classroom (name, created_at) VALUES ('t', 't0');"
    ).lastrowid
    return conn.execute(
        "INSERT INTO assignment (classroom_id, name, created_at) VALUES (?, 'a', 't0');",
        (classroom_id,),
    ).lastrowid


def _seed_training_job(conn: sqlite3.Connection) -> int:
    """classroom → assignment → training_job; devolve o job_id (a FK exige a cadeia)."""
    return conn.execute(
        "INSERT INTO training_job (assignment_id, status, created_at) VALUES (?, 'pending', 't0');",
        (_seed_assignment(conn),),
    ).lastrowid


def test_training_job_born_null_progress(tmp_path):
    """Uma linha recém-criada lê as colunas de progresso como NULL."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    job_id = _seed_training_job(conn)

    row = conn.execute(
        "SELECT total_epochs, started_at, updated_at, error_message FROM training_job "
        "WHERE id = ?;",
        (job_id,),
    ).fetchone()
    assert tuple(row) == (None, None, None, None)




def test_migration_0009_carries_existing_data_to_the_glossary_names(tmp_path):
    """0009 sobre um banco em user_version=8 com dado real: renomeia sem perder nada, preenche o
    AssignmentID do ProgSnap2 a partir do nome e traduz os estados antigos."""
    import shutil

    migrations_dir = Path(runner_mod.__file__).resolve().parent
    up_to_8 = tmp_path / "migrations_up_to_8"
    up_to_8.mkdir()
    for script in migrations_dir.glob("[0-9][0-9][0-9][0-9]_*.sql"):
        if int(script.name[:4]) <= 8:
            shutil.copy(script, up_to_8 / script.name)

    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn, migrations_dir=up_to_8)
    assert _user_version(conn) == 8
    conn.execute("INSERT INTO turma (id, name, created_at) VALUES (1, 'CSEDM', 't0');")
    conn.executemany(
        "INSERT INTO assignment (id, turma_id, name, current_version_id, created_at, status) "
        "VALUES (?, 1, ?, NULL, 't0', ?);",
        [(1, "Assignment 439", "trainable"), (2, "Assignment 492", "eda_only"), (3, "manual", "kc_draft")],
    )
    conn.execute(
        "INSERT INTO submission (assignment_id, code_state_id, subject_id, problem_id, score, "
        "created_at) VALUES (1, 'cs1', 'S1', 7, 1.0, 't0');"
    )

    run_migrations(conn)

    assert _user_version(conn) == 9
    rows = conn.execute(
        "SELECT id, classroom_id, progsnap_assignment_id, status FROM assignment ORDER BY id;"
    ).fetchall()
    assert [tuple(r) for r in rows] == [
        (1, 1, 439, "ready_for_kc_generation"),
        (2, 1, 492, "statistics_only"),
        (3, 1, None, "kc_draft"),  # nome fora do padrão da importação: fica vazio, não inventado
    ]
    assert tuple(conn.execute("SELECT id, name FROM classroom;").fetchone()) == (1, "CSEDM")
    sub = conn.execute("SELECT code_snapshot_id, student_id FROM submission;").fetchone()
    assert tuple(sub) == ("cs1", "S1")
    assert {"current_epoch", "train_loss"}.isdisjoint(_column_names(conn, "training_job"))
    assert conn.execute("PRAGMA foreign_key_check;").fetchall() == []
