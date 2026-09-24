# Interface de persistência dos vínculos entre problema e KC.
from __future__ import annotations

from typing import Protocol

from api.knowledge_components.domain.entities.problem_knowledge_component_entity import (
    ProblemKnowledgeComponent,
)


class IProblemKnowledgeComponentRepository(Protocol):
    def add(self, binding: ProblemKnowledgeComponent) -> int: ...

    def list_by_assignment(self, assignment_id: int) -> list[ProblemKnowledgeComponent]: ...

    def bind_problems(self, assignment_id: int, kc_id: int, problem_ids: list[int]) -> None:
        # Liga o KC a cada problema, um vínculo que já existe é ignorado.
        ...

    def move_bindings(self, assignment_id: int, from_kc_id: int, to_kc_id: int) -> None:
        # Problemas de `from_kc_id` passam a ser de `to_kc_id` (união, sem duplicar).
        ...

    def delete_bindings_of(self, kc_id: int) -> None: ...

    def problems_of(self, kc_id: int) -> list[int]: ...

    def count_kcs_of_problem(self, assignment_id: int, problem_id: int) -> int: ...
