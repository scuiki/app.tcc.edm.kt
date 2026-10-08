# Cria um assignment direto no banco, só com as colunas que o teste pede.

from __future__ import annotations

import sqlite3


def add_assignment(
    conn: sqlite3.Connection,
    classroom_id: int,
    *,
    name: str = "A",
    status: str | None = None,
    progsnap_assignment_id: int | None = None,
) -> int:
    # O modelo publicado entra depois, porque o model_artifact precisa do assignment antes
    return conn.execute(
        "INSERT INTO assignment (classroom_id, name, created_at, status, progsnap_assignment_id) "
        "VALUES (?, ?, 't0', ?, ?);",
        (classroom_id, name, status, progsnap_assignment_id),
    ).lastrowid
