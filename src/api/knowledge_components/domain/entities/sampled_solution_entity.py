# Uma solução que a extração escolheu para o LLM ler num problema, pela execução e pela posição.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SampledSolution:
    assignment_id: int
    problem_id: int
    position: int  # a ordem da solução no prompt, a partir de 1
    submission_id: int  # a execução escolhida, que traz o aluno, o horário e o código
