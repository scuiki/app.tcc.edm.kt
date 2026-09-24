# AssignmentInStatusRule recusa um assignment fora dos status permitidos, ou inexistente.

from __future__ import annotations

from types import SimpleNamespace

from api.assignments.domain.entities.assignment_entity import Assignment, AssignmentStatus
from api.assignments.domain.rules.assignment_in_status_rule import AssignmentInStatusRule


class _InMemoryAssignments:
    def __init__(self, *assignments: Assignment) -> None:
        self._by_id = {a.id: a for a in assignments}

    def get(self, assignment_id: int) -> Assignment | None:
        return self._by_id.get(assignment_id)


def _rule(*assignments: Assignment) -> AssignmentInStatusRule:
    return AssignmentInStatusRule(
        _InMemoryAssignments(*assignments),
        allowed=(AssignmentStatus.KC_APPROVED,),
        message="Q-matrix ainda não aprovada",
    )


def _assignment(status: AssignmentStatus) -> Assignment:
    return Assignment(id=1, classroom_id=1, name="A", created_at="t0", status=status)


def test_passes_when_the_status_is_allowed():
    rule = _rule(_assignment(AssignmentStatus.KC_APPROVED))

    assert rule.check(SimpleNamespace(assignment_id=1)) is None


def test_refuses_any_other_status():
    rule = _rule(_assignment(AssignmentStatus.KC_DRAFT))

    assert rule.check(SimpleNamespace(assignment_id=1)) == "Q-matrix ainda não aprovada"


def test_refuses_a_missing_assignment_with_the_same_message():
    assert _rule().check(SimpleNamespace(assignment_id=1)) == "Q-matrix ainda não aprovada"
