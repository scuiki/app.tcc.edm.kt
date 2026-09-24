# As rotas de /assignments/{assignment_id}, os problemas e os KCs de cada um.

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.assignments.problems.application.dtos.list_problems_dto import ListProblemsResponseDTO
from api.assignments.problems.application.use_cases.list_problems_use_case import (
    ListProblemsUseCase,
)
from api.assignments.problems.presentation import dependencies
from api.knowledge_components.application.dtos.list_problem_knowledge_components_dto import (
    ListProblemKnowledgeComponentsResponseDTO,
)
from api.knowledge_components.application.use_cases.list_problem_knowledge_components_use_case import (
    ListProblemKnowledgeComponentsUseCase,
)

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
    "/problems/knowledge-components",
    response_model=ListProblemKnowledgeComponentsResponseDTO,
    description="Cada problema do assignment com a descrição e os KCs que ele exige.",
)
def list_problem_knowledge_components(
    assignment_id: int,
    use_case: ListProblemKnowledgeComponentsUseCase = Depends(dependencies.list_problem_knowledge_components_use_case),
) -> ListProblemKnowledgeComponentsResponseDTO:
    return use_case.execute(assignment_id)
