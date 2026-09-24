# IClassroomRepository sobre SQLite; a turma é a raiz por professor, tudo pende dela.

from __future__ import annotations

import sqlite3

from api.assignments.domain.entities.classroom_entity import Classroom


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
            "SELECT id, name, created_at FROM classroom WHERE id = ?;", (classroom_id,)
        ).fetchone()
        return None if row is None else _to_entity(row)

    def list_all(self) -> list[Classroom]:
        rows = self._conn.execute("SELECT id, name, created_at FROM classroom ORDER BY id;")
        return [_to_entity(r) for r in rows]
