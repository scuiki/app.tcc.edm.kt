# IUnitOfWork sobre uma conexão SQLite, BEGIN IMMEDIATE ao entrar, COMMIT ou ROLLBACK ao sair.

from __future__ import annotations

import sqlite3

from api.shared.infrastructure.database.sqlite_connection import transaction


class SqliteUnitOfWork:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._transaction = None

    def __enter__(self) -> "SqliteUnitOfWork":
        self._transaction = transaction(self._conn)
        self._transaction.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool | None:
        return self._transaction.__exit__(exc_type, exc, tb)
