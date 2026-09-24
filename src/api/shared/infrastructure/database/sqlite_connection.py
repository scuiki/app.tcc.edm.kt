# Conexão SQLite mais o context manager de transação explícita, primeiro I/O SQLite do projeto.
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator


# isolation_level=None ativa autocommit, BEGIN/COMMIT explícitos evitam o commit implícito do DDL.
def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")  # OFF por padrão no SQLite, precisa ativar por conexão
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


# Usado pelo acquire da trava e pela troca atômica da versão corrente do artefato.
@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    # BEGIN IMMEDIATE pega o write-lock no início, não na 1ª escrita, serializando escritores.
    conn.execute("BEGIN IMMEDIATE;")
    try:
        yield conn
        conn.execute("COMMIT;")
    except BaseException:
        conn.execute("ROLLBACK;")
        raise
