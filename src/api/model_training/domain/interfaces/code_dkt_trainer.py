"""Treinar o Code-DKT (ml/). A implementação fica na infraestrutura."""

from __future__ import annotations

from typing import Callable, Protocol

from api.model_training.domain.value_objects.training_dataset import TrainingDataset
from api.model_training.domain.value_objects.training_outcome import TrainingOutcome


class ICodeDktTrainer(Protocol):
    @property
    def total_epochs(self) -> int: ...

    def train(
        self, dataset: TrainingDataset, on_epoch: Callable[[int, float], None]
    ) -> TrainingOutcome:
        """Treina e avalia; `on_epoch(época, loss_média)` é chamado ao fim de cada época."""
        ...
