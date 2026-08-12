"""Knowledge Components de um assignment (KC-02)."""

from __future__ import annotations

import sqlite3
from typing import Optional

from edmkt_app.persistence import models


class KCRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, kc: models.KC) -> int:
        cur = self._conn.execute(
            "INSERT INTO kc (assignment_id, name, kc_index) VALUES (?, ?, ?);",
            (kc.assignment_id, kc.name, kc.kc_index),
        )
        return cur.lastrowid

    def get(self, kc_id: int) -> Optional[models.KC]:
        row = self._conn.execute(
            "SELECT id, assignment_id, name, kc_index FROM kc WHERE id = ?;", (kc_id,)
        ).fetchone()
        if row is None:
            return None
        return models.KC(
            id=row["id"],
            assignment_id=row["assignment_id"],
            name=row["name"],
            kc_index=row["kc_index"],
        )

    def list_by_assignment(self, assignment_id: int) -> list[models.KC]:
        rows = self._conn.execute(
            "SELECT id, assignment_id, name, kc_index FROM kc WHERE assignment_id = ?;",
            (assignment_id,),
        ).fetchall()
        return [
            models.KC(
                id=r["id"],
                assignment_id=r["assignment_id"],
                name=r["name"],
                kc_index=r["kc_index"],
            )
            for r in rows
        ]

    def rename(self, kc_id: int, name: str) -> None:
        # name é dado do professor (KC-02): parametrizado `?`, nunca interpolado (V5/T-05-11).
        self._conn.execute("UPDATE kc SET name = ? WHERE id = ?;", (name, kc_id))

    def delete(self, kc_id: int) -> None:
        self._conn.execute("DELETE FROM kc WHERE id = ?;", (kc_id,))
