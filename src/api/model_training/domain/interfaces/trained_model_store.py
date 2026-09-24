"""Guardar a versão treinada. A implementação (arquivos em disco + linha no banco) fica na infraestrutura."""

from __future__ import annotations

from typing import Protocol

from api.model_training.domain.value_objects.training_dataset import TrainingDataset
from api.model_training.domain.value_objects.training_outcome import TrainingOutcome


class ITrainedModelStore(Protocol):
    def save(self, dataset: TrainingDataset, assignment_id: int, outcome: TrainingOutcome) -> int:
        """Grava os arquivos (write-once) e a linha da versão; devolve o id. NÃO publica."""
        ...
