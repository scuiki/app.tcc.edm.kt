"""KnowledgeComponentGenerationJobRepository sobre SQLite (tabela `kc_job`)."""

from __future__ import annotations

import sqlite3

from api.knowledge_components.domain.kc_generation_job_entity import (
    KnowledgeComponentGenerationJob,
)
from api.shared.domain.job_status import JobStatus


class SqliteKnowledgeComponentGenerationJobRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, job: KnowledgeComponentGenerationJob) -> int:
        cur = self._conn.execute(
            "INSERT INTO kc_job (assignment_id, status, created_at) VALUES (?, ?, ?);",
            (job.assignment_id, str(job.status), job.created_at),
        )
        return cur.lastrowid

    def get(self, job_id: int) -> KnowledgeComponentGenerationJob | None:
        row = self._conn.execute(
            "SELECT id, assignment_id, status, created_at, stage, started_at, updated_at, "
            "error_message FROM kc_job WHERE id = ?;",
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        return KnowledgeComponentGenerationJob(
            id=row["id"],
            assignment_id=row["assignment_id"],
            status=JobStatus(row["status"]),
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
            "UPDATE kc_job SET stage = ?, updated_at = ? WHERE id = ?;", (stage, updated_at, job_id)
        )

    def mark_done(self, job_id: int, updated_at: str) -> None:
        self._conn.execute(
            "UPDATE kc_job SET status = 'done', updated_at = ? WHERE id = ?;", (updated_at, job_id)
        )

    def mark_failed(self, job_id: int, error_message: str) -> None:
        self._conn.execute(
            "UPDATE kc_job SET status = 'failed', error_message = ? WHERE id = ?;",
            (error_message, job_id),
        )
