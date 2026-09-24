# Os dois KCs de uma fusão pertencem ao assignment do pedido, é regra de autorização.
from __future__ import annotations

from typing import Any

from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)


class KnowledgeComponentsBelongToAssignmentRule:
    def __init__(self, knowledge_components: IKnowledgeComponentRepository) -> None:
        self._knowledge_components = knowledge_components

    def check(self, dto: Any) -> str | None:
        keep = self._knowledge_components.get(dto.keep_kc_id)
        drop = self._knowledge_components.get(dto.drop_kc_id)
        if keep is None or drop is None:
            return None
        if keep.assignment_id != dto.assignment_id or drop.assignment_id != dto.assignment_id:
            return "KC não pertence ao assignment"
        return None
