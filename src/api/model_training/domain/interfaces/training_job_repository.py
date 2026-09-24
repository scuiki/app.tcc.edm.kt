"""A interface de persistência dos jobs de treino: a ponte entre o web e o subprocess."""

from __future__ import annotations

from typing import Protocol

from api.model_training.domain.entities.training_job_entity import TrainingJob


class ITrainingJobRepository(Protocol):
    def add(self, job: TrainingJob) -> int: ...

    def get(self, job_id: int) -> TrainingJob | None: ...

    def mark_running(self, job_id: int, total_epochs: int, started_at: str) -> None: ...

    def mark_done(self, job_id: int, updated_at: str, java_parse_rate: float | None) -> None: ...

    def mark_failed(self, job_id: int, error_message: str) -> None: ...
