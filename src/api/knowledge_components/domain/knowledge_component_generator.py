"""O que a geração de KCs precisa de fora: o KCGen-KT, que chama o LLM e o ml/.

A implementação fica na infraestrutura. Aqui ficam a forma do resultado e a checagem que decide se
ele pode ser gravado.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

import pandas as pd

from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId


class ProblemWithoutKnowledgeComponent(ValueError):
    """A Q-matrix gerada deixou algum problema sem KC: o job falha e nada é gravado."""


@dataclass(frozen=True)
class GeneratedKnowledgeComponents:
    problem_ids: list[int]
    group_names: dict[int, str]  # group_index -> o nome do KC
    groups_by_problem: dict[int, list[int]]  # problem_id -> os group_index que ele exige

    def ensure_every_problem_has_a_kc(self) -> None:
        """Validar tudo, depois gravar: uma linha toda zerada reprova a Q-matrix inteira."""
        if not self.problem_ids:
            raise ProblemWithoutKnowledgeComponent(
                "Q-matrix vazia: nenhum problema correto gerou KCs"
            )
        for problem_id in self.problem_ids:
            if not self.groups_by_problem.get(problem_id):
                raise ProblemWithoutKnowledgeComponent(f"problema {problem_id} ficou sem nenhum KC")


class KnowledgeComponentGenerator(Protocol):
    def generate(
        self,
        cleaned_submissions: pd.DataFrame,
        classroom_slug: ClassroomSlug,
        progsnap_assignment_id: ProgSnapAssignmentId,
        on_stage: Callable[[str], None],
    ) -> GeneratedKnowledgeComponents:
        """Roda o KCGen-KT sobre o dado limpo; `on_stage` recebe cada etapa nomeada."""
        ...
