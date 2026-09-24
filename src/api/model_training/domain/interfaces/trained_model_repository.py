# A interface de leitura das versões de modelo. Quem grava é o ITrainedModelStore.

from __future__ import annotations

from typing import Protocol

from api.model_training.domain.entities.trained_model_entity import TrainedModel


class ITrainedModelRepository(Protocol):
    def get(self, model_id: int) -> TrainedModel | None: ...
