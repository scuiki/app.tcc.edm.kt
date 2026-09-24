"""A matriz aluno × KC da versão publicada: calculada UMA vez por versão e servida do banco.

Na primeira leitura do dashboard, prevê e grava; nas seguintes, lê o que foi gravado. A versão é
resolvida uma única vez por chamada: as linhas gravadas e o modelo carregado são sempre da MESMA
versão, mesmo que um treino publique outra entre as duas leituras. Sem modelo publicado, a matriz
vem vazia e o TrainedModelInfo vazio: "ainda não treinado" é um estado legítimo.
"""

from __future__ import annotations

from api.assignments.domain.entities.assignment_entity import Assignment
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.interfaces.classroom_repository import IClassroomRepository
from api.classroom_import.domain.interfaces.submission_repository import ISubmissionRepository
from api.knowledge_components.domain.interfaces.qmatrix_repository import IQMatrixRepository
from api.mastery_dashboard.domain.value_objects.student_mastery_matrix import StudentMasteryMatrix
from api.mastery_dashboard.domain.entities.student_mastery_entity import StudentMastery
from api.mastery_dashboard.domain.interfaces.student_mastery_repository import (
    IStudentMasteryRepository,
)
from api.mastery_dashboard.domain.value_objects.trained_model_info import TrainedModelInfo
from api.model_training.domain.interfaces.student_mastery_predictor import IStudentMasteryPredictor
from api.model_training.domain.entities.trained_model_entity import TrainedModel
from api.model_training.domain.interfaces.trained_model_repository import ITrainedModelRepository
from api.model_training.domain.services.training_dataset_loading import load_training_dataset
from api.shared.application.interfaces.unit_of_work import IUnitOfWork


class PublishedModelMastery:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        classrooms: IClassroomRepository,
        submissions: ISubmissionRepository,
        trained_models: ITrainedModelRepository,
        qmatrix: IQMatrixRepository,
        student_masteries: IStudentMasteryRepository,
        predictor: IStudentMasteryPredictor,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._classrooms = classrooms
        self._submissions = submissions
        self._trained_models = trained_models
        self._qmatrix = qmatrix
        self._student_masteries = student_masteries
        self._predictor = predictor
        self._unit_of_work = unit_of_work

    def of(self, assignment: Assignment) -> tuple[StudentMasteryMatrix, TrainedModelInfo]:
        if assignment.published_model_id is None:
            return {}, TrainedModelInfo.not_trained()
        model = self._trained_models.get(assignment.published_model_id)
        if model is None:
            return {}, TrainedModelInfo.not_trained()
        return (
            self._load_or_compute(assignment, model),
            TrainedModelInfo(first_attempt_auc=model.first_attempt_auc, trained_at=model.created_at),
        )

    def _load_or_compute(self, assignment: Assignment, model: TrainedModel) -> StudentMasteryMatrix:
        if self._student_masteries.count_by_model(model.id) > 0:
            return {
                (m.student_id, m.kc_id): m.mastery
                for m in self._student_masteries.list_by_model(model.id)
            }

        # O mesmo recorte do treino (só Run.Program): inferir sobre outro dado produziria a matriz
        # de uma distribuição diferente da que o AUC exibido mediu.
        dataset = load_training_dataset(
            assignment.id, self._assignments, self._classrooms, self._submissions
        )
        kcs_by_problem: dict[int, list[int]] = {}
        for binding in self._qmatrix.list_by_assignment(assignment.id):
            kcs_by_problem.setdefault(binding.problem_id, []).append(binding.kc_id)
        matrix = self._predictor.predict_mastery(model, dataset, kcs_by_problem)

        # Numa transação: uma falha no meio deixaria uma matriz parcial que as próximas leituras
        # serviriam para sempre como se fosse a completa.
        with self._unit_of_work:
            for (student_id, kc_id), mastery in matrix.items():
                self._student_masteries.add(
                    StudentMastery(
                        id=None,
                        trained_model_id=model.id,
                        student_id=student_id,
                        kc_id=kc_id,
                        mastery=float(mastery),
                    )
                )
        return matrix
