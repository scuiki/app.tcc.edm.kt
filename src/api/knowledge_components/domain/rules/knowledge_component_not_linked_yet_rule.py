# Ligar um KC a um problema que ele já exige é recusado, em vez de passar calado.

from __future__ import annotations

from typing import Any

from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)


class KnowledgeComponentNotLinkedYetRule:
    def __init__(self, problem_kcs: IProblemKnowledgeComponentRepository) -> None:
        self._problem_kcs = problem_kcs

    def check(self, dto: Any) -> str | None:
        if self._problem_kcs.is_linked(dto.assignment_id, dto.kc_id, dto.problem_id):
            return f"o KC já está ligado ao problema {dto.problem_id}"
        return None
