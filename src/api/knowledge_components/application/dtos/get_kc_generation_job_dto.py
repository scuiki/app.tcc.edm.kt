# Resposta de GET /knowledge-components/generation-jobs/{job_id}.
from __future__ import annotations

from pydantic import BaseModel

from api.shared.domain.value_objects.job_status import JobStatus


class KnowledgeComponentGenerationJobDTO(BaseModel):
    job_id: int
    status: JobStatus
    stage: str | None  # generate | cluster | qmatrix | evidence | translate
    error_message: str | None
    # Dentro do estágio, quantos problemas ou grupos já terminaram e de quantos
    progress_done: int | None
    progress_total: int | None
