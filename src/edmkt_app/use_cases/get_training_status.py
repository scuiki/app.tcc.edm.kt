"""Progresso do treino em andamento (D-04): leitura WAL concorrente ao subprocess."""

from __future__ import annotations

import sqlite3

from edmkt_app.persistence import repositories as repos
from edmkt_app.use_cases.base import NotFound


class GetTrainingStatusUseCase:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, job_id: int) -> dict:
        job = repos.TrainingJobRepository(self._conn).get(job_id)
        if job is None:
            raise NotFound("job inexistente")
        return {
            "job_id": job.id,
            "status": job.status,
            "current_epoch": job.current_epoch,
            "total_epochs": job.total_epochs,
            "train_loss": job.train_loss,
            "error_message": job.error_message,
            "parse_rate": job.parse_rate,  # cobertura de parse javalang, exposta ao professor
        }
