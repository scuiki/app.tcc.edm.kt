# Lista os assignments para o professor escolher qual acompanhar.

from __future__ import annotations

from api.assignments.application.dtos.list_assignments_dto import (
    AssignmentSummaryDTO,
    ListAssignmentsResponseDTO,
)
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository


class ListAssignmentsUseCase:
    def __init__(self, assignments: IAssignmentRepository) -> None:
        self._assignments = assignments

    def execute(self) -> ListAssignmentsResponseDTO:
        return ListAssignmentsResponseDTO(
            assignments=[
                AssignmentSummaryDTO(
                    id=assignment.id,
                    progsnap_assignment_id=assignment.progsnap_assignment_id,
                    name=assignment.name,
                    status=assignment.status,
                    published_model_id=assignment.published_model_id,
                )
                for assignment in self._assignments.list_all()
            ]
        )
