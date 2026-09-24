# GET /assignments, HTTP puro; recebe, delega ao use case, devolve.

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.assignments.application.dtos.list_assignments_dto import ListAssignmentsResponseDTO
from api.assignments.application.use_cases.list_assignments_use_case import ListAssignmentsUseCase
from api.assignments.presentation.dependencies import list_assignments_use_case

router = APIRouter(tags=["assignments"])


@router.get(
    "/assignments",
    response_model=ListAssignmentsResponseDTO,
    description="Os assignments ativos; com `classroom_id`, só os daquela turma.",
)
def list_assignments(
    classroom_id: int | None = None,
    use_case: ListAssignmentsUseCase = Depends(list_assignments_use_case),
) -> ListAssignmentsResponseDTO:
    return use_case.execute(classroom_id)
