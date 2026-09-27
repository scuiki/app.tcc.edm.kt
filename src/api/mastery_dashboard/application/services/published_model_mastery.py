# A matriz é calculada uma vez por versão publicada e servida do banco nas leituras seguintes.

from __future__ import annotations

from api.assignments.domain.entities.assignment_entity import Assignment
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.classroom_import.domain.interfaces.submission_repository import ISubmissionRepository
from api.mastery_dashboard.domain.value_objects.student_mastery_matrix import StudentMasteryMatrix
from api.mastery_dashboard.domain.entities.student_mastery_entity import StudentMastery
from api.mastery_dashboard.domain.interfaces.student_mastery_repository import (
    IStudentMasteryRepository,
)
from api.model_training.domain.interfaces.student_mastery_predictor import IStudentMasteryPredictor
from api.model_training.domain.entities.trained_model_entity import TrainedModel
from api.model_training.domain.interfaces.trained_model_repository import ITrainedModelRepository
from api.model_training.domain.services.training_dataset_loading import load_training_dataset
from api.shared.application.interfaces.unit_of_work import IUnitOfWork


class PublishedModelMastery:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        submissions: ISubmissionRepository,
        trained_models: ITrainedModelRepository,
        student_masteries: IStudentMasteryRepository,
        predictor: IStudentMasteryPredictor,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._submissions = submissions
        self._trained_models = trained_models
        self._student_masteries = student_masteries
        self._predictor = predictor
        self._unit_of_work = unit_of_work

    def of(self, assignment: Assignment) -> tuple[StudentMasteryMatrix, TrainedModel | None]:
        # A versão publicada é resolvida uma vez por chamada, para não misturar versões.
        if assignment.published_model_id is None:
            return {}, None
        model = self._trained_models.get(assignment.published_model_id)
        if model is None:
            return {}, None
        return self._load_or_compute(assignment, model), model

    def _load_or_compute(self, assignment: Assignment, model: TrainedModel) -> StudentMasteryMatrix:
        if self._student_masteries.count_by_model(model.id) > 0:
            return {
                (m.student_id, m.problem_id): m.mastery
                for m in self._student_masteries.list_by_model(model.id)
            }

        # O mesmo recorte do treino, só Run.Program, senão a matriz sairia de outra distribuição.
        dataset = load_training_dataset(
            assignment.id, self._assignments, self._submissions
        )
        matrix = self._predictor.predict_current_mastery(model, dataset)

        # Em transação, senão uma falha no meio serviria a matriz parcial para sempre como completa.
        with self._unit_of_work:
            for (student_id, problem_id), mastery in matrix.items():
                self._student_masteries.add(
                    StudentMastery(
                        id=None,
                        trained_model_id=model.id,
                        student_id=student_id,
                        problem_id=problem_id,
                        mastery=float(mastery),
                    )
                )
        return matrix
