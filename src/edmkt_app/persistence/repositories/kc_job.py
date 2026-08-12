"""Job de KC-gen: espelha training_job, mas com estágio textual em vez de época (D-05)."""

from __future__ import annotations

import sqlite3
from typing import Optional

from edmkt_app.persistence import models


class KCJobRepository:
    """Linha de estado do job KCGen-KT (D-05) — espelha TrainingJobRepository, mas o progresso
    é um 'stage' textual (sample/generate/cluster/label/qmatrix) em vez de épocas numéricas.
    Round-trip à mão; todo SQL parametrizado com `?` (V5/T-05-02). insert via lastrowid (Pitfall 7).
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, job: models.KCJob) -> int:
        cur = self._conn.execute(
            "INSERT INTO kc_job (assignment_id, status, created_at) VALUES (?, ?, ?);",
            (job.assignment_id, job.status, job.created_at),
        )
        return cur.lastrowid

    def get(self, job_id: int) -> Optional[models.KCJob]:
        row = self._conn.execute(
            "SELECT id, assignment_id, status, created_at, stage, started_at, "
            "updated_at, error_message FROM kc_job WHERE id = ?;",
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        return models.KCJob(
            id=row["id"],
            assignment_id=row["assignment_id"],
            status=row["status"],
            created_at=row["created_at"],
            stage=row["stage"],
            started_at=row["started_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"],
        )

    def mark_running(self, job_id: int, started_at: str) -> None:
        self._conn.execute(
            "UPDATE kc_job SET status = 'running', started_at = ? WHERE id = ?;",
            (started_at, job_id),
        )

    def update_stage(self, job_id: int, stage: str, updated_at: str) -> None:
        self._conn.execute(
            "UPDATE kc_job SET stage = ?, updated_at = ? WHERE id = ?;",
            (stage, updated_at, job_id),
        )

    def mark_done(self, job_id: int, updated_at: str) -> None:
        self._conn.execute(
            "UPDATE kc_job SET status = 'done', updated_at = ? WHERE id = ?;",
            (updated_at, job_id),
        )

    def mark_failed(self, job_id: int, error_message: str) -> None:
        self._conn.execute(
            "UPDATE kc_job SET status = 'failed', error_message = ? WHERE id = ?;",
            (error_message, job_id),
        )
