"""Curva de loss por época de um treino (migração 0008).

Endpoint próprio, não embutido no GET /training/{job_id}: o poll de progresso roda de segundos
em segundos e tem vida curta; o histórico é lido uma vez, depois que acabou. Vidas diferentes,
recursos diferentes.
"""

from __future__ import annotations

import sqlite3

from edmkt_app.persistence import repositories as repos
from api.shared.domain.errors import NotFound


class GetTrainingHistoryUseCase:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, job_id: int) -> dict:
        if repos.TrainingJobRepository(self._conn).get(job_id) is None:
            raise NotFound("job inexistente")
        return {
            "job_id": job_id,
            "metrics": repos.TrainingMetricRepository(self._conn).list_by_job(job_id),
        }
