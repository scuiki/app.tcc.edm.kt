# Rota própria (o progresso é polled a cada poucos segundos); a curva de loss se lê uma vez.

from __future__ import annotations

from api.model_training.application.dtos.get_training_job_dto import (
    TrainingEpochMetricDTO,
    TrainingLossHistoryDTO,
)
from api.model_training.domain.interfaces.training_epoch_metric_repository import (
    ITrainingEpochMetricRepository,
)
from api.model_training.domain.interfaces.training_job_repository import ITrainingJobRepository
from api.shared.domain.errors.not_found import NotFound


class GetTrainingLossHistoryUseCase:
    def __init__(
        self, jobs: ITrainingJobRepository, epoch_metrics: ITrainingEpochMetricRepository
    ) -> None:
        self._jobs = jobs
        self._epoch_metrics = epoch_metrics

    def execute(self, job_id: int) -> TrainingLossHistoryDTO:
        if self._jobs.get(job_id) is None:
            raise NotFound("job inexistente")
        return TrainingLossHistoryDTO(
            job_id=job_id,
            epochs=[
                TrainingEpochMetricDTO(
                    epoch=m.epoch, train_loss=m.train_loss, recorded_at=m.recorded_at
                )
                for m in self._epoch_metrics.list_by_job(job_id)
            ],
        )
