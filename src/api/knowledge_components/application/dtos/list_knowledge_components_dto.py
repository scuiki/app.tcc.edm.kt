# A resposta de GET /knowledge-components, cada KC com os problemas a que ele se liga.

from __future__ import annotations

from pydantic import BaseModel


class KnowledgeComponentWithProblemsDTO(BaseModel):
    id: int
    name: str
    problem_ids: list[int]  # os ProblemID do dataset, em ordem


class ListKnowledgeComponentsResponseDTO(BaseModel):
    assignment_id: int
    knowledge_components: list[KnowledgeComponentWithProblemsDTO]
