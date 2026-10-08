# A resposta de GET /assignments/{assignment_id}/problems/knowledge-components.

from __future__ import annotations

from pydantic import BaseModel

from api.assignments.domain.value_objects.assignment_status import AssignmentStatus
from api.knowledge_components.application.dtos.edit_knowledge_components_dto import (
    KnowledgeComponentDTO,
)


class ProblemKnowledgeComponentsDTO(BaseModel):
    problem_id: int
    statement: str | None
    correct_run_count: int  # 0 se ninguém acertou o problema
    knowledge_components: list[KnowledgeComponentDTO]  # vazia se o problema ainda não tem KC


class ListProblemKnowledgeComponentsResponseDTO(BaseModel):
    assignment_id: int
    status: AssignmentStatus | None
    extracted_at: str | None  # nula sem extração concluída
    problems: list[ProblemKnowledgeComponentsDTO]
