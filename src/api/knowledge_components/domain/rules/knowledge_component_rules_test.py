# Regras de edição e aprovação dos KCs, com repositórios em memória.
from __future__ import annotations

from types import SimpleNamespace

from api.assignments.domain.entities.assignment_entity import Assignment
from api.assignments.domain.value_objects.assignment_status import AssignmentStatus
from api.assignments.problems.domain.entities.problem_entity import Problem
from api.knowledge_components.domain.rules.assignment_has_knowledge_components_rule import (
    AssignmentHasKnowledgeComponentsRule,
)
from api.knowledge_components.domain.rules.assignment_is_kc_draft_rule import (
    AssignmentIsKcDraftRule,
)
from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.entities.problem_knowledge_component_entity import (
    ProblemKnowledgeComponent,
)
from api.knowledge_components.domain.rules.every_problem_has_a_knowledge_component_rule import (
    EveryProblemHasAKnowledgeComponentRule,
)
from api.knowledge_components.domain.rules.problems_belong_to_assignment_rule import (
    ProblemsBelongToAssignmentRule,
)


class _InMemoryKnowledgeComponents:
    def __init__(self, *kcs: KnowledgeComponent) -> None:
        self._by_id = {kc.id: kc for kc in kcs}

    def get(self, kc_id: int) -> KnowledgeComponent | None:
        return self._by_id.get(kc_id)

    def list_by_assignment(self, assignment_id: int) -> list[KnowledgeComponent]:
        return [kc for kc in self._by_id.values() if kc.assignment_id == assignment_id]


class _InMemoryAssignments:
    def __init__(self, *assignments: Assignment) -> None:
        self._by_id = {a.id: a for a in assignments}

    def get(self, assignment_id: int) -> Assignment | None:
        return self._by_id.get(assignment_id)


def _kc(kc_id: int, assignment_id: int) -> KnowledgeComponent:
    return KnowledgeComponent(id=kc_id, assignment_id=assignment_id, name=f"KC {kc_id}")


def test_an_empty_draft_cannot_be_approved():
    rule = AssignmentHasKnowledgeComponentsRule(_InMemoryKnowledgeComponents(_kc(1, 20)))

    assert rule.check(SimpleNamespace(assignment_id=10)) == "assignment não tem nenhum KC para aprovar"
    assert rule.check(SimpleNamespace(assignment_id=20)) is None


def test_only_a_draft_can_be_approved_and_the_refusal_names_the_status():
    ready = Assignment(
        id=1, classroom_id=1, name="A", created_at="t0",
        status=AssignmentStatus.READY_FOR_KC_GENERATION,
    )
    draft = Assignment(id=2, classroom_id=1, name="B", created_at="t0", status=AssignmentStatus.KC_DRAFT)
    rule = AssignmentIsKcDraftRule(_InMemoryAssignments(ready, draft))

    assert rule.check(SimpleNamespace(assignment_id=1)) == (
        "assignment não está em kc_draft (status atual: ready_for_kc_generation)"
    )
    assert rule.check(SimpleNamespace(assignment_id=2)) is None
    assert rule.check(SimpleNamespace(assignment_id=99)) is None  # inexistência é NotFound


class _InMemoryProblems:
    def __init__(self, *problems: Problem) -> None:
        self._problems = problems

    def list_by_assignment(self, assignment_id: int) -> list[Problem]:
        return [p for p in self._problems if p.assignment_id == assignment_id]


def test_a_new_kc_can_only_bind_problems_of_its_assignment():
    problems = _InMemoryProblems(Problem(7, 1), Problem(7, 2), Problem(8, 3))
    rule = ProblemsBelongToAssignmentRule(problems)

    assert rule.check(SimpleNamespace(assignment_id=7, problem_ids=[1, 2])) is None
    assert rule.check(SimpleNamespace(assignment_id=7, problem_ids=[2, 3, 9])) == (
        "problemas que não existem no assignment [3, 9]"
    )


class _InMemoryProblemKnowledgeComponents:
    def __init__(self, *bindings: ProblemKnowledgeComponent) -> None:
        self._bindings = bindings

    def list_by_assignment(self, assignment_id: int) -> list[ProblemKnowledgeComponent]:
        return [b for b in self._bindings if b.assignment_id == assignment_id]


def _binding(assignment_id: int, kc_id: int, problem_id: int) -> ProblemKnowledgeComponent:
    return ProblemKnowledgeComponent(
        id=None, assignment_id=assignment_id, kc_id=kc_id, problem_id=problem_id
    )


def test_approval_needs_a_concept_on_every_problem_and_the_refusal_lists_them():
    rule = EveryProblemHasAKnowledgeComponentRule(
        _InMemoryProblems(Problem(7, 1), Problem(7, 2), Problem(7, 3), Problem(8, 1)),
        _InMemoryKnowledgeComponents(_kc(1, 7), _kc(2, 8)),
        _InMemoryProblemKnowledgeComponents(_binding(7, 1, 2), _binding(8, 2, 1)),
    )

    assert rule.check(SimpleNamespace(assignment_id=7)) == "problemas sem nenhum KC [1, 3]"
    assert rule.check(SimpleNamespace(assignment_id=8)) is None


def test_the_rule_of_every_problem_is_silent_without_any_concept():
    # Sem conceito fica só a recusa do rascunho vazio, e o exercício que não existe já é o 404
    rule = EveryProblemHasAKnowledgeComponentRule(
        _InMemoryProblems(Problem(7, 1), Problem(7, 2), Problem(8, 1)),
        _InMemoryKnowledgeComponents(_kc(1, 8)),
        _InMemoryProblemKnowledgeComponents(_binding(8, 1, 1)),
    )

    assert rule.check(SimpleNamespace(assignment_id=7)) is None
