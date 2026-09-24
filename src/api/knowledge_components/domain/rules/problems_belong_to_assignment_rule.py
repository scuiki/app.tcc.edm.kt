# Os problemas que um KC novo liga são do assignment do pedido, senão a FK recusaria com um 500.

from __future__ import annotations

from typing import Any

from api.assignments.problems.domain.interfaces.problem_repository import IProblemRepository


class ProblemsBelongToAssignmentRule:
    def __init__(self, problems: IProblemRepository) -> None:
        self._problems = problems

    def check(self, dto: Any) -> str | None:
        known = {p.problem_id for p in self._problems.list_by_assignment(dto.assignment_id)}
        unknown = sorted(set(dto.problem_ids) - known)
        if unknown:
            return f"problemas que não existem no assignment {unknown}"
        return None
