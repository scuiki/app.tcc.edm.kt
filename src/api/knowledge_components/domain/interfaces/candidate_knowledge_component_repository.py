# A persistência dos KCs candidatos. A implementação SQLite fica na infraestrutura.

from __future__ import annotations

from typing import Protocol

from api.knowledge_components.domain.entities.candidate_knowledge_component_entity import (
    CandidateKnowledgeComponent,
)


class ICandidateKnowledgeComponentRepository(Protocol):
    def add_many(self, candidates: list[CandidateKnowledgeComponent]) -> None: ...

    def list_by_assignment(self, assignment_id: int) -> list[CandidateKnowledgeComponent]: ...
