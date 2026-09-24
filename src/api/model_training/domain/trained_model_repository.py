"""A interface de leitura das versões de modelo. Quem grava é o TrainedModelStore."""

from __future__ import annotations

from typing import Protocol

from api.model_training.domain.trained_model_entity import TrainedModel


class TrainedModelRepository(Protocol):
    def get(self, model_id: int) -> TrainedModel | None: ...
