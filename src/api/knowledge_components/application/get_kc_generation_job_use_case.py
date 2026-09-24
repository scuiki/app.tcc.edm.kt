"""O progresso de uma geração de KCs: a etapa nomeada em que o job está."""

from __future__ import annotations

from api.knowledge_components.application.get_kc_generation_job_dto import (
    KnowledgeComponentGenerationJobDTO,
)
from api.knowledge_components.domain.kc_generation_job_repository import (
    KnowledgeComponentGenerationJobRepository,
)
from api.shared.domain.errors.not_found import NotFound


class GetKnowledgeComponentGenerationJobUseCase:
    def __init__(self, jobs: KnowledgeComponentGenerationJobRepository) -> None:
        self._jobs = jobs

    def execute(self, job_id: int) -> KnowledgeComponentGenerationJobDTO:
        job = self._jobs.get(job_id)
        if job is None:
            raise NotFound("job inexistente")
        return KnowledgeComponentGenerationJobDTO(
            job_id=job.id, status=job.status, stage=job.stage, error_message=job.error_message
        )
