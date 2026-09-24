"""As respostas de GET /training-jobs/{job_id} e /training-jobs/{job_id}/loss-history."""

from __future__ import annotations

from pydantic import BaseModel

from api.shared.domain.value_objects.job_status import JobStatus


class TrainingJobDTO(BaseModel):
    job_id: int
    status: JobStatus
    current_epoch: int | None  # derivados da última época gravada, não de um campo em paralelo
    total_epochs: int | None
    train_loss: float | None
    error_message: str | None
    java_parse_rate: float | None  # quanto do código dos alunos o javalang conseguiu parsear


class TrainingEpochMetricDTO(BaseModel):
    epoch: int
    train_loss: float
    recorded_at: str


class TrainingLossHistoryDTO(BaseModel):
    job_id: int
    epochs: list[TrainingEpochMetricDTO]
