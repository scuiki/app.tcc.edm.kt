# Pedido e resposta de POST /knowledge-components/generation-jobs.
from __future__ import annotations

from pydantic import BaseModel

from api.shared.domain.value_objects.job_status import JobStatus


class StartKnowledgeComponentGenerationDTO(BaseModel):
    # int, nunca str, o id vira argumento do subprocess e um int fecha injeção de comando na borda
    assignment_id: int


class StartedJobDTO(BaseModel):
    job_id: int
    status: JobStatus
