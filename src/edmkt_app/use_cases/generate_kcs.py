"""Dispara o pipeline KCGen-KT em subprocess (KC-01, D-05)."""

from __future__ import annotations

from pydantic import BaseModel

from edmkt_app import specs
from edmkt_app.background_jobs import launch_worker
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.lock import pipeline_busy
from edmkt_app.use_cases.base import BaseWriteUseCase, PipelineBusy
from edmkt_app.clock import utc_now_iso


class GenerateKCsDto(BaseModel):
    assignment_id: int  # ASVS V5: int, nunca string — fecha command injection na borda (T-05-CMD)


class GenerateKCsUseCase(BaseWriteUseCase):
    specs = [
        # KC-gen roda sobre um assignment com as duas classes e ainda-não-rascunhado (gate da Fase 3).
        specs.AssignmentInStatus(
            allowed=("ready_for_kc_generation",),
            message="assignment não está pronto para gerar KCs",
        )
    ]

    def _run(self, dto: GenerateKCsDto) -> dict:
        if pipeline_busy(self._conn):
            raise PipelineBusy("pipeline ocupado; aguarde o job atual")

        job_id = repos.KCJobRepository(self._conn).insert(
            models.KCJob(
                id=None,
                assignment_id=dto.assignment_id,
                status="pending",
                created_at=utc_now_iso(),
            )
        )
        launch_worker("edmkt_app.kc_pipeline", dto.assignment_id, job_id)
        return {"job_id": job_id, "status": "pending"}
