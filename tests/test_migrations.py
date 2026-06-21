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


def test_runner_applies_in_order(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    assert _user_version(conn) == 0
    run_migrations(conn)
    assert _user_version(conn) == 1
    assert _ALL_TABLES <= _table_names(conn)


def test_runner_idempotent(tmp_path):
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    # Second pass must not re-execute the DDL ("table already exists") nor bump again.
    run_migrations(conn)
    assert _user_version(conn) == 1


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


def test_default_migrations_dir_is_package_local(tmp_path):
    """run_migrations() with no dir argument resolves the package's own migrations/."""
    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)  # uses the default dir
    assert _user_version(conn) == 1
    # The default dir is the package's migrations folder (sanity on the resolution).
    assert runner_mod._default_migrations_dir().name == "migrations"
