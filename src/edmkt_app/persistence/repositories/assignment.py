"""Assignment e seu ciclo de status (trainable → kc_draft → kc_approved → trained)."""

from __future__ import annotations

import sqlite3
from typing import Optional

from edmkt_app.persistence import models


class AssignmentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, assignment: models.Assignment) -> int:
        cur = self._conn.execute(
            "INSERT INTO assignment (turma_id, name, current_version_id, created_at, status) "
            "VALUES (?, ?, ?, ?, ?);",
            (
                assignment.turma_id,
                assignment.name,
                assignment.current_version_id,
                assignment.created_at,
                assignment.status,
            ),
        )
        return cur.lastrowid

    def get(self, assignment_id: int) -> Optional[models.Assignment]:
        row = self._conn.execute(
            "SELECT id, turma_id, name, current_version_id, created_at, status "
            "FROM assignment WHERE id = ?;",
            (assignment_id,),
        ).fetchone()
        if row is None:
            return None
        return models.Assignment(
            id=row["id"],
            turma_id=row["turma_id"],
            name=row["name"],
            current_version_id=row["current_version_id"],
            created_at=row["created_at"],
            status=row["status"],
        )

    def set_status(self, assignment_id: int, status: str) -> None:
        # status é dado de borda (kc_draft/kc_approved/...) — parametrizado, nunca interpolado.
        self._conn.execute(
            "UPDATE assignment SET status = ? WHERE id = ?;", (status, assignment_id)
        )

    def set_current_version(self, assignment_id: int, model_artifact_id: int) -> None:
        self._conn.execute(
            "UPDATE assignment SET current_version_id = ? WHERE id = ?;",
            (model_artifact_id, assignment_id),
        )

    def list_all(self) -> list[models.Assignment]:
        # Listagem completa (BACKLOG 999.2): mesma forma de KCRepository.list_by_assignment, sem
        # filtro. Ordena por id para um payload determinístico. SQL sem parâmetros de entrada.
        rows = self._conn.execute(
            "SELECT id, turma_id, name, current_version_id, created_at, status "
            "FROM assignment ORDER BY id;"
        ).fetchall()
        return [
            models.Assignment(
                id=r["id"],
                turma_id=r["turma_id"],
                name=r["name"],
                current_version_id=r["current_version_id"],
                created_at=r["created_at"],
                status=r["status"],
            )
            for r in rows
        ]
