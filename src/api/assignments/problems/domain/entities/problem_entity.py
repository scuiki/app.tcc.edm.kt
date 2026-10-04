# Um problema de um assignment, identificado pelo ProblemID do dataset dentro do assignment.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    assignment_id: int
    problem_id: int  # o ProblemID do dataset, único só dentro do assignment
    description: str | None = None  # a que o LLM deduzia nas extrações antigas, hoje não gravada
    statement: str | None = None  # o enunciado do arquivo de enunciados, quando o pacote o traz
