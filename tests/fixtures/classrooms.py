# Cria uma turma direto no banco, como pré-requisito dos assignments de um teste.

from __future__ import annotations

import sqlite3


def add_classroom(conn: sqlite3.Connection, *, name: str = "T") -> int:
    return conn.execute(
        "INSERT INTO classroom (name, created_at) VALUES (?, 't0');", (name,)
    ).lastrowid
