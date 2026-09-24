"""As regras de edição e aprovação da Q-matrix, com repositórios em memória."""

from __future__ import annotations

from types import SimpleNamespace

from api.assignments.domain.entities.assignment_entity import Assignment, AssignmentStatus
from api.knowledge_components.domain.assignment_has_knowledge_components_rule import (
    AssignmentHasKnowledgeComponentsRule,
)
from api.knowledge_components.domain.assignment_is_kc_draft_rule import AssignmentIsKcDraftRule
from api.knowledge_components.domain.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.knowledge_components_are_distinct_rule import (
    KnowledgeComponentsAreDistinctRule,
)
from api.knowledge_components.domain.knowledge_components_belong_to_assignment_rule import (
    KnowledgeComponentsBelongToAssignmentRule,
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


def test_a_kc_cannot_be_merged_with_itself():
    rule = KnowledgeComponentsAreDistinctRule()

    assert rule.check(SimpleNamespace(keep_kc_id=7, drop_kc_id=7)) == (
        "keep_kc_id e drop_kc_id são o mesmo KC"
    )
    assert rule.check(SimpleNamespace(keep_kc_id=7, drop_kc_id=8)) is None


def test_both_kcs_of_a_merge_must_belong_to_the_assignment():
    rule = KnowledgeComponentsBelongToAssignmentRule(
        _InMemoryKnowledgeComponents(_kc(1, assignment_id=10), _kc(2, assignment_id=20))
    )

    refused = rule.check(SimpleNamespace(assignment_id=10, keep_kc_id=1, drop_kc_id=2))
    assert refused == "KC não pertence ao assignment"


def test_the_ownership_rule_is_silent_about_a_missing_kc():
    # A inexistência é NotFound (levantado antes pelo use case), não regra violada.
    rule = KnowledgeComponentsBelongToAssignmentRule(_InMemoryKnowledgeComponents())

    assert rule.check(SimpleNamespace(assignment_id=10, keep_kc_id=1, drop_kc_id=2)) is None


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
