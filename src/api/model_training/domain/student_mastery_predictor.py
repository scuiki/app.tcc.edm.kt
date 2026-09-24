"""O que o dashboard precisa do modelo: a mastery de cada aluno em cada KC.

Declarada aqui (quem sabe carregar e rodar um modelo treinado é model_training) e usada pelo
dashboard. A implementação recarrega a versão, prevê por PROBLEMA e agrega por KC pela Q-matrix: a
saída do Code-DKT é por problema, e o professor lê por KC.
"""

from __future__ import annotations

from typing import Protocol

from api.model_training.domain.trained_model_entity import TrainedModel
from api.model_training.domain.training_dataset import TrainingDataset


class StudentMasteryPredictor(Protocol):
    def predict_mastery(
        self,
        trained_model: TrainedModel,
        dataset: TrainingDataset,
        kcs_by_problem: dict[int, list[int]],
    ) -> dict[tuple[str, int], float]:
        """{(student_id, kc_id): mastery}; `kcs_by_problem` é a Q-matrix aprovada."""
        ...
