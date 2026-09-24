"""Dispara o treino Code-DKT em subprocess (MODEL-01/02, D-02)."""

from __future__ import annotations

from pydantic import BaseModel

from edmkt_app import specs
from edmkt_app.background_jobs import launch_worker
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.lock import pipeline_busy
from edmkt_app.use_cases.base import BaseWriteUseCase, PipelineBusy
from edmkt_app.clock import utc_now_iso


class StartTrainingDto(BaseModel):
    assignment_id: int  # ASVS V5: int, nunca string — fecha command injection na borda (T-04-INPUT)


class StartTrainingUseCase(BaseWriteUseCase):
    specs = [
        # KC-03: sem treino antes da aprovação da Q-matrix pelo professor. O fluxo de estado é
        # trainable → kc_draft → kc_approved → trained.
        specs.AssignmentInStatus(
            allowed=("kc_approved",), message="Q-matrix ainda não aprovada pelo professor"
        )
    ]

    def _run(self, dto: StartTrainingDto) -> dict:
        # Fora do registry de propósito: corrida, não regra do payload (ver PipelineBusy).
        if pipeline_busy(self._conn):
            raise PipelineBusy("pipeline ocupado; aguarde o treino atual")

        job_id = repos.TrainingJobRepository(self._conn).insert(
            models.TrainingJob(
                id=None,
                assignment_id=dto.assignment_id,
                status="pending",
                created_at=utc_now_iso(),
            )
        )
        launch_worker("edmkt_app.train", dto.assignment_id, job_id)
        return {"job_id": job_id, "status": "pending"}
