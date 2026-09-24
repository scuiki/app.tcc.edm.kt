# A persistência dos problemas. A implementação SQLite fica na infraestrutura.

from __future__ import annotations

from typing import Protocol

from api.assignments.problems.domain.entities.problem_entity import Problem


class IProblemRepository(Protocol):
    def add_many(self, problems: list[Problem]) -> None: ...

    def list_by_assignment(self, assignment_id: int) -> list[Problem]: ...

    def set_descriptions(self, assignment_id: int, descriptions: dict[int, str]) -> None: ...
