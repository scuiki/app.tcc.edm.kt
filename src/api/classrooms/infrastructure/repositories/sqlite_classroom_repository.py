# IClassroomRepository sobre SQLite; as leituras ignoram as turmas excluídas.

from __future__ import annotations

import sqlite3

from api.classrooms.domain.entities.classroom_entity import Classroom


def _to_entity(row: sqlite3.Row) -> Classroom:
    return Classroom(id=row["id"], name=row["name"], created_at=row["created_at"])


class SqliteClassroomRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, classroom: Classroom) -> int:
        cur = self._conn.execute(
            "INSERT INTO classroom (name, created_at) VALUES (?, ?);",
            (classroom.name, classroom.created_at),
        )
        return cur.lastrowid

    def get(self, classroom_id: int) -> Classroom | None:
        row = self._conn.execute(
            "SELECT id, name, created_at FROM classroom WHERE id = ? AND deleted_at IS NULL;",
            (classroom_id,),
        ).fetchone()
        return None if row is None else _to_entity(row)

    def list_all(self) -> list[Classroom]:
        rows = self._conn.execute(
            "SELECT id, name, created_at FROM classroom WHERE deleted_at IS NULL ORDER BY id;"
        )
        return [_to_entity(r) for r in rows]

    def rename(self, classroom_id: int, name: str) -> None:
        self._conn.execute(
            "UPDATE classroom SET name = ? WHERE id = ? AND deleted_at IS NULL;",
            (name, classroom_id),
        )

    def remove(self, classroom_id: int, removed_at: str) -> None:
        self._conn.execute(
            "UPDATE classroom SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL;",
            (removed_at, classroom_id),
        )
