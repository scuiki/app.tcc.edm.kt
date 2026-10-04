# A persistência das soluções amostradas. A implementação SQLite fica na infraestrutura.

from __future__ import annotations

from typing import Protocol

from api.knowledge_components.domain.entities.sampled_solution_entity import SampledSolution


class ISampledSolutionRepository(Protocol):
    def add_many(self, solutions: list[SampledSolution]) -> None: ...

    def list_by_assignment(self, assignment_id: int) -> list[SampledSolution]: ...
