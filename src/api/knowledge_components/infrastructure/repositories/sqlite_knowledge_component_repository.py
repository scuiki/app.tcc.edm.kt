# IKnowledgeComponentRepository sobre SQLite (tabela `kc`); as leituras ignoram os removidos.
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
            "SELECT id, assignment_id, name, kc_index FROM kc WHERE id = ? AND deleted_at IS NULL;",
            (kc_id,),
        ).fetchone()
        return None if row is None else _to_entity(row)

    def list_by_assignment(self, assignment_id: int) -> list[KnowledgeComponent]:
        rows = self._conn.execute(
            "SELECT id, assignment_id, name, kc_index FROM kc "
            "WHERE assignment_id = ? AND deleted_at IS NULL ORDER BY id;",
            (assignment_id,),
        ).fetchall()
        return [_to_entity(r) for r in rows]

    def rename(self, kc_id: int, name: str) -> None:
        # Nome vem do professor, parametrizado, nunca interpolado.
        self._conn.execute(
            "UPDATE kc SET name = ? WHERE id = ? AND deleted_at IS NULL;", (name, kc_id)
        )

    def remove(self, kc_id: int, removed_at: str) -> None:
        self._conn.execute(
            "UPDATE kc SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL;",
            (removed_at, kc_id),
        )

    def names_including_removed(self, assignment_id: int) -> dict[int, str]:
        # Um modelo treinado antes de uma remoção ainda prevê o KC removido, e o nome dele fica
        rows = self._conn.execute(
            "SELECT id, name FROM kc WHERE assignment_id = ?;", (assignment_id,)
        ).fetchall()
        return {r["id"]: r["name"] for r in rows}
