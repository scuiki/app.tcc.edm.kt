# Leitura do estado da trava de job, direto no banco, para os testes.

from __future__ import annotations

import sqlite3


def lock_holder_pid(conn: sqlite3.Connection) -> int | None:
    return conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()["holder_pid"]
