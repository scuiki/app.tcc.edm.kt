# Um id inexistente cai na mesma mensagem de status errado (409), por design herdado.

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
