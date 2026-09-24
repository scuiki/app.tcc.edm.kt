# O assignment alvo de um pedido, ou NotFound, o 404 com que todo use case começa.

from __future__ import annotations

from api.assignments.domain.entities.assignment_entity import Assignment
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.shared.domain.errors.not_found import NotFound


def get_existing_assignment(repository: IAssignmentRepository, assignment_id: int) -> Assignment:
    assignment = repository.get(assignment_id)
    if assignment is None:
        raise NotFound("assignment inexistente")
    return assignment
