# Os conceitos ativos do exercício e os vínculos com os problemas, nos dois sentidos, com nome.

from __future__ import annotations

from dataclasses import dataclass, field

from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)


@dataclass(frozen=True)
class ConceptBindings:
    names: dict[int, str] = field(default_factory=dict)
    kcs_by_problem: dict[int, list[int]] = field(default_factory=dict)
    problems_by_kc: dict[int, list[int]] = field(default_factory=dict)

    def name_of(self, kc_id: int) -> str:
        return self.names.get(kc_id, f"KC {kc_id}")


def load_concept_bindings(
    assignment_id: int,
    knowledge_components: IKnowledgeComponentRepository,
    problem_kcs: IProblemKnowledgeComponentRepository,
) -> ConceptBindings:
    # Depois do treino os vínculos não mudam, então os ativos são os que o modelo conheceu.
    names = {kc.id: kc.name for kc in knowledge_components.list_by_assignment(assignment_id)}
    kcs_by_problem: dict[int, list[int]] = {}
    problems_by_kc: dict[int, list[int]] = {}
    for binding in problem_kcs.list_by_assignment(assignment_id):
        kcs_by_problem.setdefault(binding.problem_id, []).append(binding.kc_id)
        problems_by_kc.setdefault(binding.kc_id, []).append(binding.problem_id)
    return ConceptBindings(
        names=names,
        kcs_by_problem={p: sorted(kcs) for p, kcs in kcs_by_problem.items()},
        problems_by_kc={k: sorted(ps) for k, ps in problems_by_kc.items()},
    )
