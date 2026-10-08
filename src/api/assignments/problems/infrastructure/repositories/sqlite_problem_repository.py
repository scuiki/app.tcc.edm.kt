# IProblemRepository sobre SQLite, na tabela `problem`.

from __future__ import annotations

import sqlite3

from api.assignments.problems.domain.entities.problem_entity import Problem


class SqliteProblemRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add_many(self, problems: list[Problem]) -> None:
        self._conn.executemany(
            "INSERT INTO problem (assignment_id, problem_id, statement) VALUES (?, ?, ?);",
            [(p.assignment_id, p.problem_id, p.statement) for p in problems],
        )

    def list_by_assignment(self, assignment_id: int) -> list[Problem]:
        rows = self._conn.execute(
            "SELECT assignment_id, problem_id, statement FROM problem "
            "WHERE assignment_id = ? ORDER BY problem_id;",
            (assignment_id,),
        ).fetchall()
        return [Problem(r["assignment_id"], r["problem_id"], r["statement"]) for r in rows]
