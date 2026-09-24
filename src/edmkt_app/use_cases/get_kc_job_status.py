"""Progresso do KCGen-KT: estágio nomeado em vez de época numérica (D-05)."""

from __future__ import annotations

import sqlite3

from edmkt_app.persistence import repositories as repos
from api.shared.domain.errors import NotFound


class GetKCJobStatusUseCase:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, job_id: int) -> dict:
        job = repos.KCJobRepository(self._conn).get(job_id)
        if job is None:
            raise NotFound("job inexistente")
        return {
            "job_id": job.id,
            "status": job.status,
            "stage": job.stage,
            "error_message": job.error_message,
        }
