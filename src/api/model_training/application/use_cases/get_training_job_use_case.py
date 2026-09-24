"""O progresso de um treino, lido enquanto o subprocess escreve (WAL)."""

from __future__ import annotations

from api.model_training.application.dtos.get_training_job_dto import TrainingJobDTO
from api.model_training.domain.interfaces.training_epoch_metric_repository import (
    ITrainingEpochMetricRepository,
)
from api.model_training.domain.interfaces.training_job_repository import ITrainingJobRepository
from api.shared.domain.errors.not_found import NotFound


class GetTrainingJobUseCase:
    def __init__(
        self, jobs: ITrainingJobRepository, epoch_metrics: ITrainingEpochMetricRepository
    ) -> None:
        self._jobs = jobs
        self._epoch_metrics = epoch_metrics

    def execute(self, job_id: int) -> TrainingJobDTO:
        job = self._jobs.get(job_id)
        if job is None:
            raise NotFound("job inexistente")
        last = self._epoch_metrics.last(job_id)
        return TrainingJobDTO(
            job_id=job.id,
            status=job.status,
            current_epoch=None if last is None else last.epoch,
            total_epochs=job.total_epochs,
            train_loss=None if last is None else last.train_loss,
            error_message=job.error_message,
            java_parse_rate=job.java_parse_rate,
        )
