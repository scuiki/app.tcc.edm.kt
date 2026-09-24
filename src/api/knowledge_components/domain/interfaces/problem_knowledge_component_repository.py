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

    def is_linked(self, assignment_id: int, kc_id: int, problem_id: int) -> bool: ...

    def move_bindings(
        self, assignment_id: int, from_kc_id: int, to_kc_id: int, removed_at: str
    ) -> None:
        # Problemas de `from_kc_id` passam a ser de `to_kc_id` (união, sem duplicar)
        ...

    def remove(self, assignment_id: int, kc_id: int, problem_id: int, removed_at: str) -> bool:
        # Marca o vínculo como removido e diz se havia um ativo
        ...

    def remove_all_of(self, kc_id: int, removed_at: str) -> None: ...

    def problems_of(self, kc_id: int) -> list[int]: ...

    def count_kcs_of_problem(self, assignment_id: int, problem_id: int) -> int: ...
