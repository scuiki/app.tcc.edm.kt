"""SQLite connection + explicit-transaction context manager (RESEARCH Pattern 1, D-03).

First SQLite I/O in the project: ml is framework-free (D-01), so this lives in the
app layer and depends inward. The connection contract (autocommit + FK ON + WAL) is the
foundation the migration runner (D-02), the pipeline lock (D-07/MODEL-03) and the atomic
flip (D-06/MODEL-04) all build on.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator


def connect(path: str) -> sqlite3.Connection:
    """Open app.db in autocommit mode with FK enforcement, WAL and a busy timeout."""
    # isolation_level=None => autocommit; we issue BEGIN/COMMIT ourselves. The default
    # sqlite3 transaction handling does NOT open a txn before DDL and commits implicitly,
    # which would break the atomic DDL+user_version bump in the migration runner (D-02).
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")  # OFF by default in SQLite — must enable per connection
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Wrap a write in BEGIN IMMEDIATE / COMMIT, rolling back on any exception.

    Consumed by the lock acquire (MODEL-03) and the current-version flip (MODEL-04).
    """
    # BEGIN IMMEDIATE grabs the write lock at the start (not on first write), serializing
    # concurrent writers so a SELECT-then-UPDATE stays atomic against other transactions.
    conn.execute("BEGIN IMMEDIATE;")
    try:
        yield conn
        conn.execute("COMMIT;")
    except BaseException:
        conn.execute("ROLLBACK;")
        raise
