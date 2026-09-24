# Cria os problemas de um assignment direto no banco, antes das tentativas e dos KCs.

from __future__ import annotations

import sqlite3


def add_problems(conn: sqlite3.Connection, assignment_id: int, problem_ids) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO problem (assignment_id, problem_id) VALUES (?, ?);",
        [(assignment_id, int(p)) for p in problem_ids],
    )
