"""A curva de loss de um treino, época por época.

Rota própria, não embutida no progresso: o poll de progresso roda de segundos em segundos e tem
vida curta; a curva é lida uma vez, depois que o treino acabou.
"""

from __future__ import annotations

from api.model_training.application.get_training_job_dto import (
    TrainingEpochMetricDTO,
    TrainingLossHistoryDTO,
)
from api.model_training.domain.training_epoch_metric_repository import (
    TrainingEpochMetricRepository,
)
from api.model_training.domain.training_job_repository import TrainingJobRepository
from api.shared.domain.errors.not_found import NotFound


class GetTrainingLossHistoryUseCase:
    def __init__(
        self, jobs: TrainingJobRepository, epoch_metrics: TrainingEpochMetricRepository
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
