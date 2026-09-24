"""Regra: um rascunho sem nenhum KC não tem Q-matrix a aprovar."""

from __future__ import annotations

from typing import Any

from api.knowledge_components.domain.knowledge_component_repository import (
    KnowledgeComponentRepository,
)


class AssignmentHasKnowledgeComponentsRule:
    def __init__(self, knowledge_components: KnowledgeComponentRepository) -> None:
        self._knowledge_components = knowledge_components

    def check(self, dto: Any) -> str | None:
        if not self._knowledge_components.list_by_assignment(dto.assignment_id):
            return "assignment não tem nenhum KC para aprovar"
        return None
