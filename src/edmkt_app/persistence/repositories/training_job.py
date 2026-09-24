"""Job de treino: a ponte SQLite entre o web e o subprocess fire-and-forget."""

from __future__ import annotations

import sqlite3
from typing import Optional

from edmkt_app.persistence import models


class TrainingJobRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, job: models.TrainingJob) -> int:
        cur = self._conn.execute(
            "INSERT INTO training_job (assignment_id, status, created_at) VALUES (?, ?, ?);",
            (job.assignment_id, job.status, job.created_at),
        )
        return cur.lastrowid

    def get(self, job_id: int) -> Optional[models.TrainingJob]:
        row = self._conn.execute(
            "SELECT id, assignment_id, status, created_at, total_epochs, "
            "started_at, updated_at, error_message, parse_rate "
            "FROM training_job WHERE id = ?;",
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        return models.TrainingJob(
            id=row["id"],
            assignment_id=row["assignment_id"],
            status=row["status"],
            created_at=row["created_at"],
            total_epochs=row["total_epochs"],
            started_at=row["started_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"],
            parse_rate=row["parse_rate"],
        )

    def mark_running(self, job_id: int, total_epochs: int, started_at: str) -> None:
        self._conn.execute(
            "UPDATE training_job SET status = 'running', total_epochs = ?, started_at = ? WHERE id = ?;",
            (total_epochs, started_at, job_id),
        )

    def mark_done(
        self, job_id: int, updated_at: str, parse_rate: Optional[float] = None
    ) -> None:
        # parse_rate default None preserva os callers existentes; quando o subprocess o fornece,
        # grava na mesma transição de sucesso (D-06 estendido/MODEL-05). SQL parametrizado (T-04-04).
        if parse_rate is None:
            self._conn.execute(
                "UPDATE training_job SET status = 'done', updated_at = ? WHERE id = ?;",
                (updated_at, job_id),
            )
        else:
            self._conn.execute(
                "UPDATE training_job SET status = 'done', updated_at = ?, parse_rate = ? WHERE id = ?;",
                (updated_at, parse_rate, job_id),
            )

    def mark_failed(self, job_id: int, error_message: str) -> None:
        self._conn.execute(
            "UPDATE training_job SET status = 'failed', error_message = ? WHERE id = ?;",
            (error_message, job_id),
        )
