# IStudentMasteryRepository sobre SQLite (tabela `mastery_prediction`).

from __future__ import annotations

import sqlite3

from api.mastery_dashboard.domain.entities.student_mastery_entity import StudentMastery


class SqliteStudentMasteryRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, student_mastery: StudentMastery) -> int:
        cur = self._conn.execute(
            "INSERT INTO mastery_prediction (model_artifact_id, student_id, kc_id, mastery) "
            "VALUES (?, ?, ?, ?);",
            (
                student_mastery.trained_model_id,
                student_mastery.student_id,
                student_mastery.kc_id,
                student_mastery.mastery,
            ),
        )
        return cur.lastrowid

    def count_by_model(self, trained_model_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM mastery_prediction WHERE model_artifact_id = ?;",
            (trained_model_id,),
        ).fetchone()
        return row["n"]

    def list_by_model(self, trained_model_id: int) -> list[StudentMastery]:
        rows = self._conn.execute(
            "SELECT id, model_artifact_id, student_id, kc_id, mastery FROM mastery_prediction "
            "WHERE model_artifact_id = ?;",
            (trained_model_id,),
        ).fetchall()
        return [
            StudentMastery(
                id=r["id"],
                trained_model_id=r["model_artifact_id"],
                student_id=r["student_id"],
                kc_id=r["kc_id"],
                mastery=r["mastery"],
            )
            for r in rows
        ]
