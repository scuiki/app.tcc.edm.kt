"""As estatísticas pré-treino de um assignment: disponíveis desde a importação, sem modelo."""

from __future__ import annotations

from api.assignments.domain.assignment_repository import AssignmentRepository
from api.assignments.domain.classroom_repository import ClassroomRepository
from api.assignments.domain.classroom_slug import ClassroomSlug
from api.assignments.domain.existing_assignment import get_existing_assignment
from api.assignments.domain.progsnap_assignment_id import ProgSnapAssignmentId
from api.classroom_import.domain.cleaned_submissions_store import CleanedSubmissionsStore
from api.mastery_dashboard.application.mastery_dashboard_dto import (
    PreTrainingStatisticsResponseDTO,
)
from api.mastery_dashboard.domain.pre_training_statistics import PreTrainingStatistics
from api.shared.domain.errors import NotFound


class GetPreTrainingStatisticsUseCase:
    def __init__(
        self,
        assignments: AssignmentRepository,
        classrooms: ClassroomRepository,
        cleaned_submissions: CleanedSubmissionsStore,
    ) -> None:
        self._assignments = assignments
        self._classrooms = classrooms
        self._cleaned_submissions = cleaned_submissions

    def execute(self, assignment_id: int) -> PreTrainingStatisticsResponseDTO:
        assignment = get_existing_assignment(self._assignments, assignment_id)
        classroom = self._classrooms.get(assignment.classroom_id)
        if classroom is None:  # turma órfã: 404 explícito, não AttributeError em .name
            raise NotFound("turma inexistente")

        slug = ClassroomSlug.from_name(classroom.name)
        progsnap_id = ProgSnapAssignmentId(assignment.progsnap_assignment_id)
        # Sem o dado limpo ainda, estatísticas vazias: a tela resiste à falta de dado, não só de
        # modelo. Leem o dado INTEIRO (com Compile.Error): a taxa de erro de compilação depende
        # justamente do que o recorte de treino remove.
        statistics = (
            PreTrainingStatistics.of(self._cleaned_submissions.read(slug, progsnap_id))
            if self._cleaned_submissions.exists(slug, progsnap_id)
            else PreTrainingStatistics.empty()
        )
        return PreTrainingStatisticsResponseDTO(
            assignment_id=assignment_id,
            success_rate=statistics.success_rate,
            learning_curve=statistics.learning_curve,
            compile_error_rate=statistics.compile_error_rate,
        )
