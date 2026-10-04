# ISampledSolutionRepository sobre SQLite, na tabela `sampled_solution`.

from __future__ import annotations

import sqlite3

from api.knowledge_components.domain.entities.sampled_solution_entity import SampledSolution


class SqliteSampledSolutionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add_many(self, solutions: list[SampledSolution]) -> None:
        self._conn.executemany(
            "INSERT INTO sampled_solution (assignment_id, problem_id, position, submission_id) "
            "VALUES (?, ?, ?, ?);",
            [(s.assignment_id, s.problem_id, s.position, s.submission_id) for s in solutions],
        )

    def list_by_assignment(self, assignment_id: int) -> list[SampledSolution]:
        rows = self._conn.execute(
            "SELECT assignment_id, problem_id, position, submission_id FROM sampled_solution "
            "WHERE assignment_id = ? ORDER BY problem_id, position;",
            (assignment_id,),
        ).fetchall()
        return [
            SampledSolution(r["assignment_id"], r["problem_id"], r["position"], r["submission_id"])
            for r in rows
        ]
