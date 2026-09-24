"""AssignmentRepository sobre SQLite. Todo SQL é parametrizado; nenhum dado é interpolado."""

from __future__ import annotations

import sqlite3

from api.assignments.domain.assignment_entity import Assignment, AssignmentStatus

_COLUMNS = (
    "id, classroom_id, name, published_model_id, created_at, status, progsnap_assignment_id"
)


def _to_entity(row: sqlite3.Row) -> Assignment:
    return Assignment(
        id=row["id"],
        classroom_id=row["classroom_id"],
        name=row["name"],
        created_at=row["created_at"],
        status=None if row["status"] is None else AssignmentStatus(row["status"]),
        progsnap_assignment_id=row["progsnap_assignment_id"],
        published_model_id=row["published_model_id"],
    )


class SqliteAssignmentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, assignment: Assignment) -> int:
        cur = self._conn.execute(
            "INSERT INTO assignment "
            "(classroom_id, name, published_model_id, created_at, status, progsnap_assignment_id) "
            "VALUES (?, ?, ?, ?, ?, ?);",
            (
                assignment.classroom_id,
                assignment.name,
                assignment.published_model_id,
                assignment.created_at,
                None if assignment.status is None else str(assignment.status),
                assignment.progsnap_assignment_id,
            ),
        )
        return cur.lastrowid

    def get(self, assignment_id: int) -> Assignment | None:
        row = self._conn.execute(
            f"SELECT {_COLUMNS} FROM assignment WHERE id = ?;", (assignment_id,)
        ).fetchone()
        return None if row is None else _to_entity(row)

    def list_all(self) -> list[Assignment]:
        # Ordenado por id: payload determinístico.
        rows = self._conn.execute(f"SELECT {_COLUMNS} FROM assignment ORDER BY id;").fetchall()
        return [_to_entity(r) for r in rows]

    def set_status(self, assignment_id: int, status: AssignmentStatus) -> None:
        self._conn.execute(
            "UPDATE assignment SET status = ? WHERE id = ?;", (str(status), assignment_id)
        )

    def set_published_model(self, assignment_id: int, model_id: int) -> None:
        self._conn.execute(
            "UPDATE assignment SET published_model_id = ? WHERE id = ?;", (model_id, assignment_id)
        )
