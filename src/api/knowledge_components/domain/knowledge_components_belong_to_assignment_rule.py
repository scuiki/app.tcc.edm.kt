"""Regra: os dois KCs de uma fusão pertencem ao assignment do pedido.

É autorização: sem ela, apagar o KC fundido apagaria um KC de OUTRO assignment (o DELETE não
filtra por assignment), deixando vínculo pendurado na Q-matrix alheia. A inexistência de um KC é
NotFound, levantado antes pelo use case; aqui não é regra violada.
"""

from __future__ import annotations

from typing import Any

from api.knowledge_components.domain.knowledge_component_repository import (
    KnowledgeComponentRepository,
)


class KnowledgeComponentsBelongToAssignmentRule:
    def __init__(self, knowledge_components: KnowledgeComponentRepository) -> None:
        self._knowledge_components = knowledge_components

    def check(self, dto: Any) -> str | None:
        keep = self._knowledge_components.get(dto.keep_kc_id)
        drop = self._knowledge_components.get(dto.drop_kc_id)
        if keep is None or drop is None:
            return None
        if keep.assignment_id != dto.assignment_id or drop.assignment_id != dto.assignment_id:
            return "KC não pertence ao assignment"
        return None
