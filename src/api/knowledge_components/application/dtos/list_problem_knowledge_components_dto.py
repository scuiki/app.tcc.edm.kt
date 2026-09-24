# A resposta de GET /assignments/{assignment_id}/problems/knowledge-components.

from __future__ import annotations

from pydantic import BaseModel

from api.assignments.domain.entities.assignment_entity import AssignmentStatus
from api.knowledge_components.application.dtos.edit_knowledge_components_dto import (
    KnowledgeComponentDTO,
)


class ProblemKnowledgeComponentsDTO(BaseModel):
    problem_id: int
    description: str | None
    knowledge_components: list[KnowledgeComponentDTO]  # vazia se o problema ainda não tem KC


class ListProblemKnowledgeComponentsResponseDTO(BaseModel):
    assignment_id: int
    status: AssignmentStatus | None
    problems: list[ProblemKnowledgeComponentsDTO]
