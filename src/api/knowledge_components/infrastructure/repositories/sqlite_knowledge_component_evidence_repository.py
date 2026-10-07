# IKnowledgeComponentEvidenceRepository sobre SQLite, na tabela `kc_evidence`.

from __future__ import annotations

import sqlite3

from api.knowledge_components.domain.entities.knowledge_component_evidence_entity import (
    KnowledgeComponentEvidence,
)

_COLUMNS = "assignment_id, problem_id, kc_id, position, first_line, last_line"


class SqliteKnowledgeComponentEvidenceRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add_many(self, evidence: list[KnowledgeComponentEvidence]) -> None:
        self._conn.executemany(
            f"INSERT INTO kc_evidence ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?);",
            [
                (e.assignment_id, e.problem_id, e.kc_id, e.position, e.first_line, e.last_line)
                for e in evidence
            ],
        )

    def list_by_assignment(self, assignment_id: int) -> list[KnowledgeComponentEvidence]:
        rows = self._conn.execute(
            f"SELECT {_COLUMNS} FROM kc_evidence "
            "WHERE assignment_id = ? ORDER BY problem_id, kc_id;",
            (assignment_id,),
        ).fetchall()
        return [KnowledgeComponentEvidence(**dict(r)) for r in rows]
