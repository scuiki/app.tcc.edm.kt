# Testa a conexão SQLite mais o runner de migrations, base da persistência. Hermético e CPU-only.
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from api.shared.infrastructure.database.migrations.runner import run_migrations
from api.shared.infrastructure.database.sqlite_connection import connect
from api.shared.infrastructure.database.migrations import runner as runner_mod

# As 8 entidades do domínio, mais a tabela dedicada de trava de uma linha só.
_DOMAIN_TABLES = {
    "classroom",
    "assignment",
    "submission",
    "kc",
    "problem",
    "problem_kc",
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


# Derivada dos arquivos, não um literal, senão cada migration nova quebraria este teste por
_LATEST_VERSION = max(
    int(f.name[:4])
    for f in (Path(__file__).resolve().parent / "migrations").glob("[0-9][0-9][0-9][0-9]_*.sql")
)

# As colunas de progresso que sobrevivem de 0003 no training_job; current_epoch e train_loss
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
    # Uma segunda passada não pode reexecutar o DDL nem bumpar de novo.
    run_migrations(conn)
    assert _user_version(conn) == _LATEST_VERSION


# Um passo com DDL inválido dá ROLLBACK, user_version não avança além do último passo bom.
def test_runner_bumps_atomically(tmp_path):
    migrations_dir = tmp_path / "migs"
    migrations_dir.mkdir()
    # Passo propositalmente quebrado, avança até o primeiro statement e falha no segundo.
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
    # O bump não pode ter acontecido, o passo inteiro faz rollback.
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


# Um comentário `--` inline com `;` dentro não pode quebrar o split nem truncar `--` numa string.
def test_inline_comment_does_not_break_split(tmp_path):
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
    # `--` dentro da string literal foi preservado, não truncado pelo strip de comentário.
    row = conn.execute("SELECT label FROM foo WHERE id=1;").fetchone()
    assert row["label"] == "a--b"


def test_default_migrations_dir_is_package_local(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)  # usa a pasta default
    assert _user_version(conn) == _LATEST_VERSION
    # A pasta default é a migrations/ do próprio pacote.
    assert runner_mod._default_migrations_dir().name == "migrations"


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table});")}


def test_migration_0002_grows_assignment_and_submission(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 2
    assert "status" in _column_names(conn, "assignment")
    assert "event_type" in _column_names(conn, "submission")


def test_migration_0003_grows_training_job_progress(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 3
    assert _TRAINING_JOB_PROGRESS_COLUMNS <= _column_names(conn, "training_job")


def test_migration_0004_adds_parse_rate(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 4
    assert "parse_rate" in _column_names(conn, "training_job")


def test_migration_0005_adds_kc_index_and_kc_job(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= 5
    assert "kc_index" in _column_names(conn, "kc")
    assert "kc_job" in _table_names(conn)
    # kc_job tem a forma do job de background (espelha training_job), status mais estágio.
    assert {"id", "assignment_id", "status", "created_at", "stage", "error_message"} <= (
        _column_names(conn, "kc_job")
    )


def test_migration_0006_adds_qmatrix_unique_index(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 6))
    assert _user_version(conn) == 6
    indexes = {
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='qmatrix';"
        )
    }
    assert "uq_qmatrix_assignment_kc_problem" in indexes


def test_migration_0007_adds_first_auc(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    assert _user_version(conn) >= _LATEST_VERSION
    assert "first_attempt_auc" in _column_names(conn, "model_artifact")


def test_first_attempt_auc_is_nullable(tmp_path):
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


def test_problem_kc_unique_blocks_duplicate_binding(tmp_path):
    import sqlite3 as _sqlite3

    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    aid = _seed_assignment(conn)
    kc_id = conn.execute(
        "INSERT INTO kc (assignment_id, name) VALUES (?, 'k');", (aid,)
    ).lastrowid
    conn.execute("INSERT INTO problem (assignment_id, problem_id) VALUES (?, 7);", (aid,))
    insert = "INSERT INTO problem_kc (assignment_id, kc_id, problem_id) VALUES (?, ?, 7);"
    conn.execute(insert, (aid, kc_id))

    with pytest.raises(_sqlite3.IntegrityError):
        conn.execute(insert, (aid, kc_id))
    conn.execute(insert.replace("INSERT", "INSERT OR IGNORE"), (aid, kc_id))
    n = conn.execute("SELECT COUNT(*) FROM problem_kc;").fetchone()[0]
    assert n == 1


def test_training_job_parse_rate_round_trips(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    job_id = _seed_training_job(conn)

    conn.execute("UPDATE training_job SET parse_rate = 0.86 WHERE id = ?;", (job_id,))
    row = conn.execute("SELECT parse_rate FROM training_job WHERE id = ?;", (job_id,)).fetchone()
    assert row["parse_rate"] == 0.86


# classroom -> assignment, em SQL puro (este teste é do schema, não de um repositório).
def _seed_assignment(conn: sqlite3.Connection) -> int:
    classroom_id = conn.execute(
        "INSERT INTO classroom (name, created_at) VALUES ('t', 't0');"
    ).lastrowid
    return conn.execute(
        "INSERT INTO assignment (classroom_id, name, created_at) VALUES (?, 'a', 't0');",
        (classroom_id,),
    ).lastrowid


# classroom -> assignment -> training_job, devolve o job_id (a FK exige a cadeia).
def _seed_training_job(conn: sqlite3.Connection) -> int:
    return conn.execute(
        "INSERT INTO training_job (assignment_id, status, created_at) VALUES (?, 'pending', 't0');",
        (_seed_assignment(conn),),
    ).lastrowid


def test_training_job_born_null_progress(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    job_id = _seed_training_job(conn)

    row = conn.execute(
        "SELECT total_epochs, started_at, updated_at, error_message FROM training_job "
        "WHERE id = ?;",
        (job_id,),
    ).fetchone()
    assert tuple(row) == (None, None, None, None)


# Uma cópia da pasta de migrations só até `version`, o banco como estava naquela versão.
def _migrations_up_to(tmp_path: Path, version: int) -> Path:
    import shutil

    migrations_dir = Path(runner_mod.__file__).resolve().parent
    up_to = tmp_path / f"migrations_up_to_{version}"
    up_to.mkdir()
    for script in migrations_dir.glob("[0-9][0-9][0-9][0-9]_*.sql"):
        if int(script.name[:4]) <= version:
            shutil.copy(script, up_to / script.name)
    return up_to


# 0009 sobre um banco com dado real, renomeia sem perder nada e traduz os estados antigos.
def test_migration_0009_carries_existing_data_to_the_glossary_names(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 8))
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

    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 9))

    assert _user_version(conn) == 9
    rows = conn.execute(
        "SELECT id, classroom_id, progsnap_assignment_id, status FROM assignment ORDER BY id;"
    ).fetchall()
    assert [tuple(r) for r in rows] == [
        (1, 1, 439, "ready_for_kc_generation"),
        (2, 1, 492, "statistics_only"),
        (3, 1, None, "kc_draft"),  # nome fora do padrão da importação, fica vazio, não inventado
    ]
    assert tuple(conn.execute("SELECT id, name FROM classroom;").fetchone()) == (1, "CSEDM")
    sub = conn.execute("SELECT code_snapshot_id, student_id FROM submission;").fetchone()
    assert tuple(sub) == ("cs1", "S1")
    assert {"current_epoch", "train_loss"}.isdisjoint(_column_names(conn, "training_job"))
    assert conn.execute("PRAGMA foreign_key_check;").fetchall() == []


# 0010 sobre um banco em user_version=9, submission passa a ter o dado limpo inteiro.
def test_migration_0010_moves_the_cleaned_data_into_submission(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 9))
    assignment_id = _seed_assignment(conn)
    conn.execute(
        "INSERT INTO submission (assignment_id, code_snapshot_id, student_id, problem_id, score, "
        "created_at) VALUES (?, 'cs1', 'S1', 7, 1.0, 't0');",
        (assignment_id,),
    )

    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 10))

    assert _user_version(conn) == 10
    assert _column_names(conn, "submission") == {
        "id", "assignment_id", "student_id", "problem_id", "code_snapshot_id", "code", "score",
        "submitted_at", "event_type", "is_correct",
    }
    assert conn.execute("SELECT COUNT(*) FROM submission;").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM assignment;").fetchone()[0] == 1


# 0011 sobre um banco em user_version=10, os problemas saem das tentativas e da Q-matrix.
def test_migration_0011_creates_the_problems_and_keeps_every_row(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 10))
    assignment_id = _seed_assignment(conn)
    kc_id = conn.execute(
        "INSERT INTO kc (assignment_id, name) VALUES (?, 'k');", (assignment_id,)
    ).lastrowid
    for problem_id in (7, 7, 9):
        conn.execute(
            "INSERT INTO submission (assignment_id, problem_id, submitted_at, event_type, "
            "is_correct) VALUES (?, ?, 't0', 'Run.Program', 1);",
            (assignment_id, problem_id),
        )
    conn.execute(
        "INSERT INTO qmatrix (assignment_id, kc_id, problem_id) VALUES (?, ?, 7);",
        (assignment_id, kc_id),
    )

    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 11))

    assert _user_version(conn) == 11
    problems = conn.execute("SELECT problem_id, description FROM problem ORDER BY 1;").fetchall()
    assert [tuple(r) for r in problems] == [(7, None), (9, None)]
    assert conn.execute("SELECT COUNT(*) FROM submission;").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM qmatrix;").fetchone()[0] == 1
    assert conn.execute("PRAGMA foreign_key_check;").fetchall() == []
    # Agora um vínculo com um problema que não existe é recusado pelo banco
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO qmatrix (assignment_id, kc_id, problem_id) VALUES (?, ?, 99);",
            (assignment_id, kc_id),
        )


# 0012 sobre um banco em user_version=11, a tabela qmatrix vira problem_kc sem perder vínculos.
def test_migration_0012_renames_qmatrix_to_problem_kc(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 11))
    assignment_id = _seed_assignment(conn)
    kc_id = conn.execute(
        "INSERT INTO kc (assignment_id, name) VALUES (?, 'k');", (assignment_id,)
    ).lastrowid
    conn.execute("INSERT INTO problem (assignment_id, problem_id) VALUES (?, 7);", (assignment_id,))
    conn.execute(
        "INSERT INTO qmatrix (assignment_id, kc_id, problem_id) VALUES (?, ?, 7);",
        (assignment_id, kc_id),
    )

    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 12))

    assert _user_version(conn) == 12
    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';")}
    assert "problem_kc" in tables and "qmatrix" not in tables
    assert conn.execute("SELECT COUNT(*) FROM problem_kc;").fetchone()[0] == 1
    indexes = {
        r["name"]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE tbl_name='problem_kc';")
    }
    assert "uq_problem_kc" in indexes
    assert conn.execute("PRAGMA foreign_key_check;").fetchall() == []


# 0013 sobre um banco em user_version=12, deleted_at em kc e problem_kc, e o índice parcial.
def test_migration_0013_adds_soft_delete_and_a_partial_unique_index(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn, migrations_dir=_migrations_up_to(tmp_path, 12))
    assignment_id = _seed_assignment(conn)
    kc_id = conn.execute(
        "INSERT INTO kc (assignment_id, name) VALUES (?, 'k');", (assignment_id,)
    ).lastrowid
    conn.execute("INSERT INTO problem (assignment_id, problem_id) VALUES (?, 7);", (assignment_id,))
    insert = "INSERT INTO problem_kc (assignment_id, kc_id, problem_id) VALUES (?, ?, 7);"
    conn.execute(insert, (assignment_id, kc_id))

    run_migrations(conn)

    assert _user_version(conn) == 13
    assert "deleted_at" in _column_names(conn, "kc")
    assert "deleted_at" in _column_names(conn, "problem_kc")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(insert, (assignment_id, kc_id))  # dois vínculos ativos iguais, não
    conn.execute("UPDATE problem_kc SET deleted_at = 't1';")
    conn.execute(insert, (assignment_id, kc_id))  # um removido e um ativo, sim
    assert conn.execute("SELECT COUNT(*) FROM problem_kc;").fetchone()[0] == 2

