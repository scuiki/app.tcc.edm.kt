# ITrainingJobRepository sobre SQLite (tabela `training_job`).

from __future__ import annotations

import sqlite3

from api.model_training.domain.entities.training_job_entity import TrainingJob
from api.shared.domain.value_objects.job_status import JobStatus


class SqliteTrainingJobRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, job: TrainingJob) -> int:
        cur = self._conn.execute(
            "INSERT INTO training_job (assignment_id, status, created_at) VALUES (?, ?, ?);",
            (job.assignment_id, str(job.status), job.created_at),
        )
        return cur.lastrowid

    def get(self, job_id: int) -> TrainingJob | None:
        row = self._conn.execute(
            "SELECT id, assignment_id, status, created_at, total_epochs, started_at, updated_at, "
            "error_message, parse_rate FROM training_job WHERE id = ?;",
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        return TrainingJob(
            id=row["id"],
            assignment_id=row["assignment_id"],
            status=JobStatus(row["status"]),
            created_at=row["created_at"],
            total_epochs=row["total_epochs"],
            started_at=row["started_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"],
            java_parse_rate=row["parse_rate"],
        )

    def mark_running(self, job_id: int, total_epochs: int, started_at: str) -> None:
        self._conn.execute(
            "UPDATE training_job SET status = 'running', total_epochs = ?, started_at = ? "
            "WHERE id = ?;",
            (total_epochs, started_at, job_id),
        )

    def mark_done(self, job_id: int, updated_at: str, java_parse_rate: float | None) -> None:
        # A taxa é gravada na mesma transição de sucesso, pois o retorno do subprocess se perde.
        self._conn.execute(
            "UPDATE training_job SET status = 'done', updated_at = ?, "
            "parse_rate = COALESCE(?, parse_rate) WHERE id = ?;",
            (updated_at, java_parse_rate, job_id),
        )

    def mark_failed(self, job_id: int, error_message: str) -> None:
        self._conn.execute(
            "UPDATE training_job SET status = 'failed', error_message = ? WHERE id = ?;",
            (error_message, job_id),
        )
