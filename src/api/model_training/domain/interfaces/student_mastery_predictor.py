# O dashboard lê o estado atual por aluno x problema; o conceito é derivado depois pela Q-matrix.

from __future__ import annotations

from typing import Protocol

from api.model_training.domain.entities.trained_model_entity import TrainedModel
from api.model_training.domain.value_objects.training_dataset import TrainingDataset


class IStudentMasteryPredictor(Protocol):
    def predict_current_mastery(
        self, trained_model: TrainedModel, dataset: TrainingDataset
    ) -> dict[tuple[str, int], float]:
        # `{(student_id, problem_id): mastery}`, a chance de acerto se o aluno tentasse agora.
        ...
