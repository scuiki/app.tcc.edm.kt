"""A interface de persistência das turmas. A implementação SQLite fica na infraestrutura."""

from __future__ import annotations

from typing import Protocol

from api.assignments.domain.entities.classroom_entity import Classroom


class IClassroomRepository(Protocol):
    def add(self, classroom: Classroom) -> int: ...

    def get(self, classroom_id: int) -> Classroom | None: ...

    def list_all(self) -> list[Classroom]: ...
