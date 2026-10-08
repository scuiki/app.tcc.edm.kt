# A ordem da origem do conceito, com repositórios em memória que devolvem tudo fora de ordem.
from __future__ import annotations

from types import SimpleNamespace

from api.assignments.problems.domain.entities.problem_entity import Problem
from api.knowledge_components.application.use_cases.get_knowledge_component_origin_use_case import (
    GetKnowledgeComponentOriginUseCase,
)
from api.knowledge_components.domain.entities.candidate_knowledge_component_entity import (
    CandidateKnowledgeComponent,
)
from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.entities.sampled_solution_entity import SampledSolution


def _returning(value):
    return lambda *_: value


def test_problems_reasonings_and_solutions_come_in_order_whatever_the_repositories_return():
    # No SQLite o índice dos vínculos já devolve os problemas em ordem, e só aqui a ordem muda
    kc = KnowledgeComponent(id=7, assignment_id=1, name="Laços")
    use_case = GetKnowledgeComponentOriginUseCase(
        assignments=SimpleNamespace(get=_returning(object())),
        problems=SimpleNamespace(list_by_assignment=_returning([Problem(1, 1), Problem(1, 3)])),
        knowledge_components=SimpleNamespace(get=_returning(kc)),
        problem_kcs=SimpleNamespace(problems_of=_returning([3, 1])),
        candidate_kcs=SimpleNamespace(
            list_by_assignment=_returning(
                [
                    CandidateKnowledgeComponent(1, 1, 2, "b", "b", 7, "segunda"),
                    CandidateKnowledgeComponent(1, 1, 1, "a", "a", 7, "primeira"),
                ]
            )
        ),
        evidence=SimpleNamespace(list_by_assignment=_returning([])),
        sampled_solutions=SimpleNamespace(
            list_by_assignment=_returning(
                [SampledSolution(1, 1, 2, 20), SampledSolution(1, 1, 1, 10)]
            )
        ),
        submissions=SimpleNamespace(get_codes=_returning({10: "um", 20: "dois"})),
    )

    origin = use_case.execute(7)

    assert [problem.problem_id for problem in origin.problems] == [1, 3]
    first = origin.problems[0]
    assert first.translated_reasonings == ["primeira", "segunda"]
    assert [(s.position, s.code) for s in first.sampled_solutions] == [(1, "um"), (2, "dois")]
