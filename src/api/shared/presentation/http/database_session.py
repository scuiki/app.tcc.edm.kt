# Uma conexão SQLite por requisição HTTP, abre ao entrar e fecha ao sair.
from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Request

from api.shared.infrastructure.database.sqlite_connection import connect


def open_database_session(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()
