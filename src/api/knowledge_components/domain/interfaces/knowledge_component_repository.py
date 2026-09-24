"""A interface de persistência dos KCs."""

from __future__ import annotations

from typing import Protocol

from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent


class IKnowledgeComponentRepository(Protocol):
    def add(self, knowledge_component: KnowledgeComponent) -> int: ...

    def get(self, kc_id: int) -> KnowledgeComponent | None: ...

    def list_by_assignment(self, assignment_id: int) -> list[KnowledgeComponent]: ...

    def rename(self, kc_id: int, name: str) -> None: ...

    def delete(self, kc_id: int) -> None: ...
