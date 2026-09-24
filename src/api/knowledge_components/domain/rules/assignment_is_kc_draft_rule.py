"""Regra: só se aprova um rascunho de fato.

Aprovar fora de kc_draft deixaria o treino rodar sobre uma Q-matrix inexistente, burlando a
revisão do professor. A inexistência do assignment é NotFound, levantado antes pelo use case.
"""

from __future__ import annotations

from typing import Any

from api.assignments.domain.entities.assignment_entity import AssignmentStatus
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository


class AssignmentIsKcDraftRule:
    def __init__(self, assignments: IAssignmentRepository) -> None:
        self._assignments = assignments

    def check(self, dto: Any) -> str | None:
        assignment = self._assignments.get(dto.assignment_id)
        if assignment is None:
            return None
        if assignment.status != AssignmentStatus.KC_DRAFT:
            return f"assignment não está em kc_draft (status atual: {assignment.status})"
        return None
