# As rotas de /assignments/{assignment_id}, os problemas e a Q-matrix vista por eles.

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.assignments.problems.application.dtos.list_problems_dto import ListProblemsResponseDTO
from api.assignments.problems.application.use_cases.list_problems_use_case import (
    ListProblemsUseCase,
)
from api.assignments.problems.presentation import dependencies
from api.knowledge_components.application.dtos.get_qmatrix_dto import QMatrixResponseDTO
from api.knowledge_components.application.use_cases.get_qmatrix_use_case import GetQMatrixUseCase

router = APIRouter(prefix="/assignments/{assignment_id}", tags=["problems"])


@router.get(
    "/problems",
    response_model=ListProblemsResponseDTO,
    description="Os problemas do assignment, com a descrição de cada um.",
)
def list_problems(
    assignment_id: int,
    use_case: ListProblemsUseCase = Depends(dependencies.list_problems_use_case),
) -> ListProblemsResponseDTO:
    return use_case.execute(assignment_id)


@router.get(
    "/qmatrix",
    response_model=QMatrixResponseDTO,
    description="Cada problema do assignment com a descrição e os KCs que ele exige.",
)
def get_qmatrix(
    assignment_id: int,
    use_case: GetQMatrixUseCase = Depends(dependencies.get_qmatrix_use_case),
) -> QMatrixResponseDTO:
    return use_case.execute(assignment_id)
