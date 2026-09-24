"""O pedido e a resposta de POST /training-jobs."""

from __future__ import annotations

from pydantic import BaseModel

from api.shared.domain.job_status import JobStatus


class StartTrainingDTO(BaseModel):
    # int, nunca str: o id vira argumento do subprocess, e um int fecha injeção de comando na borda
    assignment_id: int


class StartedTrainingJobDTO(BaseModel):
    job_id: int
    status: JobStatus
