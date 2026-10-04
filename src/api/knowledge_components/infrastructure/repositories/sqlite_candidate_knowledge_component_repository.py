# ICandidateKnowledgeComponentRepository sobre SQLite, na tabela `candidate_kc`.

from __future__ import annotations

import sqlite3

from api.knowledge_components.domain.entities.candidate_knowledge_component_entity import (
    CandidateKnowledgeComponent,
)

_COLUMNS = (
    "assignment_id, problem_id, position, name, reasoning, kc_id, translated_reasoning"
)


class SqliteCandidateKnowledgeComponentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add_many(self, candidates: list[CandidateKnowledgeComponent]) -> None:
        self._conn.executemany(
            f"INSERT INTO candidate_kc ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?);",
            [
                (
                    c.assignment_id,
                    c.problem_id,
                    c.position,
                    c.name,
                    c.reasoning,
                    c.kc_id,
                    c.translated_reasoning,
                )
                for c in candidates
            ],
        )

    def list_by_assignment(self, assignment_id: int) -> list[CandidateKnowledgeComponent]:
        rows = self._conn.execute(
            f"SELECT {_COLUMNS} FROM candidate_kc "
            "WHERE assignment_id = ? ORDER BY problem_id, position;",
            (assignment_id,),
        ).fetchall()
        return [CandidateKnowledgeComponent(**dict(r)) for r in rows]
