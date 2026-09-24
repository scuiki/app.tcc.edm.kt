# O dashboard quer mastery por aluno x KC; a impl. prevê por problema e agrega pelos KCs.

from __future__ import annotations

from typing import Protocol

from api.model_training.domain.entities.trained_model_entity import TrainedModel
from api.model_training.domain.value_objects.training_dataset import TrainingDataset


class IStudentMasteryPredictor(Protocol):
    def predict_mastery(
        self,
        trained_model: TrainedModel,
        dataset: TrainingDataset,
        kcs_by_problem: dict[int, list[int]],
    ) -> dict[tuple[str, int], float]:
        # `{(student_id, kc_id): mastery}`; `kcs_by_problem` são os KCs aprovados de cada problema.
        ...
