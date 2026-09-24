"""Matriz aluno×KC materializada por artefato (compute-once, T-06-11)."""

from __future__ import annotations

import sqlite3

from edmkt_app.persistence import models


class MasteryPredictionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, prediction: models.MasteryPrediction) -> int:
        cur = self._conn.execute(
            "INSERT INTO mastery_prediction "
            "(model_artifact_id, student_id, kc_id, mastery) VALUES (?, ?, ?, ?);",
            (
                prediction.model_artifact_id,
                prediction.subject_id,
                prediction.kc_id,
                prediction.mastery,
            ),
        )
        return cur.lastrowid

    def count_by_artifact(self, model_artifact_id: int) -> int:
        # Compute-once (T-06-11): o serviço de mastery checa se a matriz já foi materializada
        # para este artefato antes de re-inferir; >0 significa servir do SQLite, não recomputar.
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM mastery_prediction WHERE model_artifact_id = ?;",
            (model_artifact_id,),
        ).fetchone()
        return row["n"]

    def list_by_artifact(self, model_artifact_id: int) -> list[models.MasteryPrediction]:
        rows = self._conn.execute(
            "SELECT id, model_artifact_id, student_id, kc_id, mastery "
            "FROM mastery_prediction WHERE model_artifact_id = ?;",
            (model_artifact_id,),
        ).fetchall()
        return [
            models.MasteryPrediction(
                id=r["id"],
                model_artifact_id=r["model_artifact_id"],
                subject_id=r["student_id"],
                kc_id=r["kc_id"],
                mastery=r["mastery"],
            )
            for r in rows
        ]
