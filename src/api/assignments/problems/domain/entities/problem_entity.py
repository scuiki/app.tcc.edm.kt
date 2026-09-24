# Um problema de um assignment, identificado pelo ProblemID do dataset dentro do assignment.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    assignment_id: int
    problem_id: int  # o ProblemID do dataset, único só dentro do assignment
    description: str | None = None  # deduzida pelo LLM na geração de KCs, vazia até lá
