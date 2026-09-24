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
        # current_epoch/train_loss são DERIVADOS da última métrica, não campos mutáveis mantidos
        # em paralelo em training_job.
        last = repos.TrainingMetricRepository(self._conn).last(job_id)
        return {
            "job_id": job.id,
            "status": job.status,
            "current_epoch": None if last is None else last["epoch"],
            "total_epochs": job.total_epochs,
            "train_loss": None if last is None else last["train_loss"],
            "error_message": job.error_message,
            "parse_rate": job.parse_rate,  # cobertura de parse javalang, exposta ao professor
        }
