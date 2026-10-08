# Um problema sem KC ficaria fora de toda conta por conceito, e a aprovação espera ele ganhar um.

from __future__ import annotations

from typing import Any

from api.assignments.problems.domain.interfaces.problem_repository import IProblemRepository
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)


class EveryProblemHasAKnowledgeComponentRule:
    def __init__(
        self,
        problems: IProblemRepository,
        knowledge_components: IKnowledgeComponentRepository,
        problem_kcs: IProblemKnowledgeComponentRepository,
    ) -> None:
        self._problems = problems
        self._knowledge_components = knowledge_components
        self._problem_kcs = problem_kcs

    def check(self, dto: Any) -> str | None:
        # Sem nenhum KC a recusa é a do rascunho vazio, e a lista inteira dos problemas só repetiria
        if not self._knowledge_components.list_by_assignment(dto.assignment_id):
            return None
        linked = {b.problem_id for b in self._problem_kcs.list_by_assignment(dto.assignment_id)}
        known = {p.problem_id for p in self._problems.list_by_assignment(dto.assignment_id)}
        missing = sorted(known - linked)
        if missing:
            return f"problemas sem nenhum KC {missing}"
        return None
