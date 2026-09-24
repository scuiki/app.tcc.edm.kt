# Os problemas de um assignment, com a descrição de cada um.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.services.existing_assignment import get_existing_assignment
from api.assignments.problems.application.dtos.list_problems_dto import (
    ListProblemsResponseDTO,
    ProblemDTO,
)
from api.assignments.problems.domain.interfaces.problem_repository import IProblemRepository


class ListProblemsUseCase:
    def __init__(self, assignments: IAssignmentRepository, problems: IProblemRepository) -> None:
        self._assignments = assignments
        self._problems = problems

    def execute(self, assignment_id: int) -> ListProblemsResponseDTO:
        get_existing_assignment(self._assignments, assignment_id)
        return ListProblemsResponseDTO(
            assignment_id=assignment_id,
            problems=[
                ProblemDTO(problem_id=p.problem_id, description=p.description)
                for p in self._problems.list_by_assignment(assignment_id)
            ],
        )
