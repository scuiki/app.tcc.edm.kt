# As turmas ativas com o número de problemas e de alunos, e a situação de cada uma.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.problems.domain.interfaces.problem_repository import IProblemRepository
from api.classroom_import.application.dtos.list_classrooms_dto import (
    ClassroomSummaryDTO,
    ListClassroomsResponseDTO,
)
from api.classroom_import.domain.interfaces.submission_repository import ISubmissionRepository
from api.classrooms.domain.interfaces.classroom_repository import IClassroomRepository
from api.classrooms.domain.services.classroom_status_classification import (
    classify_classroom_status,
)


# Mora aqui porque os alunos só aparecem nas tentativas, que são desta funcionalidade
class ListClassroomsUseCase:
    def __init__(
        self,
        classrooms: IClassroomRepository,
        assignments: IAssignmentRepository,
        problems: IProblemRepository,
        submissions: ISubmissionRepository,
    ) -> None:
        self._classrooms = classrooms
        self._assignments = assignments
        self._problems = problems
        self._submissions = submissions

    def execute(self) -> ListClassroomsResponseDTO:
        summaries = []
        for classroom in self._classrooms.list_all():
            assignments = self._assignments.list_by_classroom(classroom.id)
            problem_count = sum(len(self._problems.list_by_assignment(a.id)) for a in assignments)
            has_published_model = any(a.published_model_id is not None for a in assignments)
            summaries.append(
                ClassroomSummaryDTO(
                    id=classroom.id,
                    name=classroom.name,
                    created_at=classroom.created_at,
                    problem_count=problem_count,
                    student_count=self._submissions.count_students([a.id for a in assignments]),
                    status=classify_classroom_status(problem_count, has_published_model),
                )
            )
        return ListClassroomsResponseDTO(classrooms=summaries)
