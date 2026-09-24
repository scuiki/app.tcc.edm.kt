"""Regra: o assignment existe E está num dos status permitidos.

Herdado, não desenho: um assignment inexistente recebe a MESMA mensagem de status errado (409), como
no contrato original do treino e da geração de KCs. Separar daria 404 para um id inexistente, mais
correto, mas é uma mudança de contrato a decidir à parte.
"""

from __future__ import annotations

from typing import Any

from api.assignments.domain.entities.assignment_entity import AssignmentStatus
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository


class AssignmentInStatusRule:
    def __init__(
        self,
        repository: IAssignmentRepository,
        allowed: tuple[AssignmentStatus, ...],
        message: str,
    ) -> None:
        self._repository = repository
        self._allowed = allowed
        self._message = message

    def check(self, dto: Any) -> str | None:
        assignment = self._repository.get(dto.assignment_id)
        if assignment is None or assignment.status not in self._allowed:
            return self._message
        return None
