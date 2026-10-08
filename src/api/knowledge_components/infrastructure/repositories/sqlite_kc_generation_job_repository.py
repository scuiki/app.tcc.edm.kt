# IKnowledgeComponentGenerationJobRepository sobre SQLite (tabela `kc_job`).
from __future__ import annotations

import sqlite3

from api.knowledge_components.domain.entities.kc_generation_job_entity import (
    KnowledgeComponentGenerationJob,
)
from api.shared.domain.value_objects.job_status import JobStatus

_COLUMNS = (
    "id, assignment_id, status, created_at, stage, started_at, updated_at, error_message, "
    "progress_done, progress_total, model_id, prompt_version"
)


def _to_entity(row: sqlite3.Row) -> KnowledgeComponentGenerationJob:
    return KnowledgeComponentGenerationJob(
        id=row["id"],
        assignment_id=row["assignment_id"],
        status=JobStatus(row["status"]),
        created_at=row["created_at"],
        stage=row["stage"],
        started_at=row["started_at"],
        updated_at=row["updated_at"],
        error_message=row["error_message"],
        progress_done=row["progress_done"],
        progress_total=row["progress_total"],
        model_id=row["model_id"],
        prompt_version=row["prompt_version"],
    )


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
            f"SELECT {_COLUMNS} FROM kc_job WHERE id = ?;", (job_id,)
        ).fetchone()
        return None if row is None else _to_entity(row)

    def find_latest_done(self, assignment_id: int) -> KnowledgeComponentGenerationJob | None:
        # O updated_at do job concluído é a hora em que o mark_done o fechou
        row = self._conn.execute(
            f"SELECT {_COLUMNS} FROM kc_job WHERE assignment_id = ? AND status = 'done' "
            "ORDER BY updated_at DESC, id DESC LIMIT 1;",
            (assignment_id,),
        ).fetchone()
        return None if row is None else _to_entity(row)

    def mark_running(self, job_id: int, started_at: str) -> None:
        self._conn.execute(
            "UPDATE kc_job SET status = 'running', started_at = ? WHERE id = ?;",
            (started_at, job_id),
        )

    def update_stage(self, job_id: int, stage: str, updated_at: str) -> None:
        # O estágio novo começa sem progresso, o do anterior não vale para ele
        self._conn.execute(
            "UPDATE kc_job SET stage = ?, progress_done = NULL, progress_total = NULL, "
            "updated_at = ? WHERE id = ?;",
            (stage, updated_at, job_id),
        )

    def update_progress(self, job_id: int, done: int, total: int, updated_at: str) -> None:
        self._conn.execute(
            "UPDATE kc_job SET progress_done = ?, progress_total = ?, updated_at = ? WHERE id = ?;",
            (done, total, updated_at, job_id),
        )

    def record_generation_model(self, job_id: int, model_id: str, prompt_version: str) -> None:
        self._conn.execute(
            "UPDATE kc_job SET model_id = ?, prompt_version = ? WHERE id = ?;",
            (model_id, prompt_version, job_id),
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
