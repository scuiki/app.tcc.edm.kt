"""Uma conexão SQLite por requisição HTTP: abre ao entrar, fecha ao sair.

O web e os subprocessos de job NUNCA compartilham um objeto Python; a coordenação é só pela linha
da OneJobAtATimeLock + WAL. Como a conexão é por requisição, os use cases também nascem por
requisição: o FastAPI resolve a cadeia `open_database_session → factory → rota` sozinho.
"""

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
