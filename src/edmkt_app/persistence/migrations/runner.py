"""Forward-only migration runner over PRAGMA user_version (D-02).

Reads the current user_version, applies each higher-numbered NNNN_*.sql step's DDL and the
user_version bump in the SAME transaction, and skips already-applied steps (idempotent).
Anti-pattern guarded against: DDL outside a transaction (a crash between DDL and bump would
corrupt the version state, RESEARCH §Anti-Patterns).
"""

from __future__ import annotations

import pathlib
import sqlite3
from typing import Optional


def _default_migrations_dir() -> pathlib.Path:
    """The package-local migrations/ folder (where the .sql steps live)."""
    return pathlib.Path(__file__).resolve().parent


def _split_statements(sql: str) -> list[str]:
    """Split a migration script into individual statements.

    executescript() issues an implicit COMMIT on entry, which would break the atomic
    DDL+bump (Open Question 2). So we run statements one at a time inside our own BEGIN
    and reserve the user_version bump for the end before COMMIT.
    """
    # Strip `--` line comments BEFORE splitting on `;` — a `;` inside a comment would
    # otherwise break the split and glue a comment fragment onto the next statement.
    no_comments = "\n".join(
        ln for ln in sql.splitlines() if not ln.strip().startswith("--")
    )
    return [stmt.strip() for stmt in no_comments.split(";") if stmt.strip()]


def run_migrations(conn: sqlite3.Connection, migrations_dir: Optional[pathlib.Path] = None) -> None:
    """Apply every NNNN_*.sql step above the current user_version, in order."""
    migrations_dir = pathlib.Path(migrations_dir) if migrations_dir else _default_migrations_dir()
    current = conn.execute("PRAGMA user_version;").fetchone()[0]
    scripts = sorted(migrations_dir.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    for script in scripts:
        version = int(script.name[:4])
        if version <= current:
            continue
        conn.execute("BEGIN IMMEDIATE;")
        try:
            for stmt in _split_statements(script.read_text()):
                conn.execute(stmt)
            # `version` is an int derived from the migration FILENAME (internal), never from
            # external input — the one controlled exception to "never interpolate SQL" (V5).
            conn.execute(f"PRAGMA user_version = {version};")
            conn.execute("COMMIT;")
        except BaseException:
            conn.execute("ROLLBACK;")
            raise
