"""A interface de persistência dos assignments. A implementação SQLite fica na infraestrutura."""

from __future__ import annotations

from typing import Protocol

from api.assignments.domain.assignment_entity import Assignment, AssignmentStatus


class AssignmentRepository(Protocol):
    def add(self, assignment: Assignment) -> int: ...

    def get(self, assignment_id: int) -> Assignment | None: ...

    def list_all(self) -> list[Assignment]: ...

    def set_status(self, assignment_id: int, status: AssignmentStatus) -> None: ...

    def set_published_model(self, assignment_id: int, model_id: int) -> None: ...
