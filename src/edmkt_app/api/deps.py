"""Dependências FastAPI: uma conexão SQLite por requisição (Pitfall 2).

Cada requisição abre a SUA conexão via `connect(db_path)` e a fecha no fim — o web e o
subprocess de treino NUNCA compartilham um objeto Python; a coordenação é só pela linha
`pipeline_lock` + WAL.
"""

from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Request

from edmkt_app.persistence import connect


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()
