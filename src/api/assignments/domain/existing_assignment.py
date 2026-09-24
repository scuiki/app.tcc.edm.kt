"""O assignment alvo de um pedido, ou NotFound: o 404 que todo use case sobre um assignment começa por."""

from __future__ import annotations

from api.assignments.domain.assignment_entity import Assignment
from api.assignments.domain.assignment_repository import AssignmentRepository
from api.shared.domain.errors import NotFound


def get_existing_assignment(repository: AssignmentRepository, assignment_id: int) -> Assignment:
    assignment = repository.get(assignment_id)
    if assignment is None:
        raise NotFound("assignment inexistente")
    return assignment
