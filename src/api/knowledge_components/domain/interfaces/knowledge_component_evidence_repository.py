# A persistência dos trechos de cada conceito. A implementação SQLite fica na infraestrutura.

from __future__ import annotations

from typing import Protocol

from api.knowledge_components.domain.entities.knowledge_component_evidence_entity import (
    KnowledgeComponentEvidence,
)


class IKnowledgeComponentEvidenceRepository(Protocol):
    def add_many(self, evidence: list[KnowledgeComponentEvidence]) -> None: ...

    def list_by_assignment(self, assignment_id: int) -> list[KnowledgeComponentEvidence]: ...
