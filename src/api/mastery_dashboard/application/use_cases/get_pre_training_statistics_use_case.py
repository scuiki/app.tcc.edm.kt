"""As estatísticas pré-treino de um assignment: disponíveis desde a importação, sem modelo."""

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.services.existing_assignment import get_existing_assignment
from api.classroom_import.domain.interfaces.submission_repository import ISubmissionRepository
from api.mastery_dashboard.application.dtos.mastery_dashboard_dto import (
    PreTrainingStatisticsResponseDTO,
)
from api.mastery_dashboard.domain.value_objects.pre_training_statistics import PreTrainingStatistics
from api.mastery_dashboard.domain.services.pre_training_statistics_calculation import (
    compute_pre_training_statistics,
)


class GetPreTrainingStatisticsUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        submissions: ISubmissionRepository,
    ) -> None:
        self._assignments = assignments
        self._submissions = submissions

    def execute(self, assignment_id: int) -> PreTrainingStatisticsResponseDTO:
        get_existing_assignment(self._assignments, assignment_id)
        # Leem o dado INTEIRO (com Compile.Error): a taxa de erro de compilação depende justamente
        # do que o recorte de treino remove. Sem dado ainda, estatísticas vazias: a tela resiste à
        # falta de dado, não só de modelo.
        submissions = self._submissions.list_by_assignment(assignment_id)
        statistics = (
            PreTrainingStatistics.empty()
            if submissions.empty
            else compute_pre_training_statistics(submissions)
        )
        return PreTrainingStatisticsResponseDTO(
            assignment_id=assignment_id,
            success_rate=statistics.success_rate,
            learning_curve=statistics.learning_curve,
            compile_error_rate=statistics.compile_error_rate,
        )
