"""O que o treino precisa de fora: treinar o Code-DKT (ml/) e guardar a versão treinada.

As implementações ficam na infraestrutura; o modelo treinado é opaco para a aplicação.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from api.model_training.domain.training_dataset import TrainingDataset


@dataclass(frozen=True)
class TrainingOutcome:
    model: object  # o CodeDKTModel treinado; só a infraestrutura sabe o que é
    vocab: dict
    hyperparameters: dict
    first_attempt_auc: float
    java_parse_rate: float


class CodeDktTrainer(Protocol):
    @property
    def total_epochs(self) -> int: ...

    def train(
        self, dataset: TrainingDataset, on_epoch: Callable[[int, float], None]
    ) -> TrainingOutcome:
        """Treina e avalia; `on_epoch(época, loss_média)` é chamado ao fim de cada época."""
        ...


class TrainedModelStore(Protocol):
    def save(self, dataset: TrainingDataset, assignment_id: int, outcome: TrainingOutcome) -> int:
        """Grava os arquivos (write-once) e a linha da versão; devolve o id. NÃO publica."""
        ...
