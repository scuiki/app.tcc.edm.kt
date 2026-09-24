"""IKnowledgeComponentRepository sobre SQLite (tabela `kc`). Todo SQL é parametrizado."""

from __future__ import annotations

import sqlite3

from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent


def _to_entity(row: sqlite3.Row) -> KnowledgeComponent:
    return KnowledgeComponent(
        id=row["id"],
        assignment_id=row["assignment_id"],
        name=row["name"],
        group_index=row["kc_index"],
    )


class SqliteKnowledgeComponentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, knowledge_component: KnowledgeComponent) -> int:
        cur = self._conn.execute(
            "INSERT INTO kc (assignment_id, name, kc_index) VALUES (?, ?, ?);",
            (
                knowledge_component.assignment_id,
                knowledge_component.name,
                knowledge_component.group_index,
            ),
        )
        return cur.lastrowid

    def get(self, kc_id: int) -> KnowledgeComponent | None:
        row = self._conn.execute(
            "SELECT id, assignment_id, name, kc_index FROM kc WHERE id = ?;", (kc_id,)
        ).fetchone()
        return None if row is None else _to_entity(row)

    def list_by_assignment(self, assignment_id: int) -> list[KnowledgeComponent]:
        rows = self._conn.execute(
            "SELECT id, assignment_id, name, kc_index FROM kc WHERE assignment_id = ?;",
            (assignment_id,),
        ).fetchall()
        return [_to_entity(r) for r in rows]

    def rename(self, kc_id: int, name: str) -> None:
        # O nome é dado do professor: parametrizado, nunca interpolado.
        self._conn.execute("UPDATE kc SET name = ? WHERE id = ?;", (name, kc_id))

    def delete(self, kc_id: int) -> None:
        self._conn.execute("DELETE FROM kc WHERE id = ?;", (kc_id,))
