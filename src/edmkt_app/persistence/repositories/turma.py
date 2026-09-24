"""Turma: a raiz por-professor; tudo pende dela."""

from __future__ import annotations

import sqlite3
from typing import Optional

from edmkt_app.persistence import models


class TurmaRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, turma: models.Turma) -> int:
        cur = self._conn.execute(
            "INSERT INTO classroom (name, created_at) VALUES (?, ?);",
            (turma.name, turma.created_at),
        )
        return cur.lastrowid

    def get(self, turma_id: int) -> Optional[models.Turma]:
        row = self._conn.execute(
            "SELECT id, name, created_at FROM classroom WHERE id = ?;", (turma_id,)
        ).fetchone()
        if row is None:
            return None
        return models.Turma(id=row["id"], name=row["name"], created_at=row["created_at"])

    def list_all(self) -> list[models.Turma]:
        return [
            models.Turma(id=r["id"], name=r["name"], created_at=r["created_at"])
            for r in self._conn.execute("SELECT id, name, created_at FROM classroom ORDER BY id;")
        ]
