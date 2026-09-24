"""Lista os assignments para o professor escolher qual acompanhar."""

from __future__ import annotations

from api.assignments.application.list_assignments_dto import (
    AssignmentSummaryDTO,
    ListAssignmentsResponseDTO,
)
from api.assignments.domain.assignment_repository import AssignmentRepository


class ListAssignmentsUseCase:
    def __init__(self, assignments: AssignmentRepository) -> None:
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
