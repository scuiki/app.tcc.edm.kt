# A interface de persistência da curva de loss, append-only, uma linha por época.

from __future__ import annotations

from typing import Protocol

from api.model_training.domain.entities.training_epoch_metric import TrainingEpochMetric


class ITrainingEpochMetricRepository(Protocol):
    def append(self, job_id: int, metric: TrainingEpochMetric) -> None: ...

    def list_by_job(self, job_id: int) -> list[TrainingEpochMetric]: ...

    def last(self, job_id: int) -> TrainingEpochMetric | None: ...
