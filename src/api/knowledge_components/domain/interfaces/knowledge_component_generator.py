# O que a geração de KCs precisa de fora, o KCGen-KT, que chama o LLM e o ml/.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

import pandas as pd


# A geração deixou algum problema sem KC, o job falha e nada é gravado.
class ProblemWithoutKnowledgeComponent(ValueError):
    pass


@dataclass(frozen=True)
class GeneratedKnowledgeComponents:
    problem_ids: list[int]
    group_names: dict[int, str]  # group_index -> o nome do KC
    groups_by_problem: dict[int, list[int]]  # problem_id -> os group_index que ele exige
    # Os KCs que o LLM listou em cada problema, na ordem da resposta, com `name` e `reasoning`
    candidate_kcs: dict[int, list[dict[str, str]]] = field(default_factory=dict)
    # O grupo em que caiu cada nome de KC candidato
    group_of_name: dict[str, int] = field(default_factory=dict)
    # As execuções que o LLM leu em cada problema, na ordem do prompt
    sampled_solutions: dict[int, list[int]] = field(default_factory=dict)
    # O modelo de linguagem e a versão do prompt que geraram os KCs
    model_id: str = ""
    prompt_version: str = ""

    def ensure_every_problem_has_a_kc(self) -> None:
        # Valida tudo antes de gravar, uma linha toda zerada reprova a geração inteira.
        if not self.problem_ids:
            raise ProblemWithoutKnowledgeComponent(
                "nenhum problema correto gerou KCs"
            )
        for problem_id in self.problem_ids:
            if not self.groups_by_problem.get(problem_id):
                raise ProblemWithoutKnowledgeComponent(f"problema {problem_id} ficou sem nenhum KC")


class IKnowledgeComponentGenerator(Protocol):
    def generate(
        self,
        correct_runs: pd.DataFrame,
        statements: dict[int, str | None],
        classroom_id: int,
        assignment_id: int,
        on_stage: Callable[[str], None],
        on_progress: Callable[[int, int], None],
    ) -> GeneratedKnowledgeComponents:
        # O KCGen-KT sobre as execuções corretas e o enunciado de cada problema, quando existe
        ...
