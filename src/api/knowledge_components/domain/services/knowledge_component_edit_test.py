# Depois do treino os KCs ficam como estão; antes dele, a edição segue livre.

from __future__ import annotations

import pytest

from api.assignments.domain.entities.assignment_entity import Assignment
from api.assignments.domain.value_objects.assignment_status import AssignmentStatus
from api.knowledge_components.domain.services.knowledge_component_edit import (
    refuse_edit_after_training,
)
from api.shared.domain.errors.business_rule_violation import BusinessRuleViolation


class _Assignments:
    def __init__(self, status: AssignmentStatus | None) -> None:
        self._status = status

    def get(self, assignment_id: int) -> Assignment | None:
        if self._status is None:
            return None
        return Assignment(id=assignment_id, classroom_id=1, name="A", created_at="t0", status=self._status)


def test_a_trained_assignment_refuses_the_edit():
    with pytest.raises(BusinessRuleViolation):
        refuse_edit_after_training(_Assignments(AssignmentStatus.TRAINED), 1)


@pytest.mark.parametrize(
    "status", [AssignmentStatus.KC_DRAFT, AssignmentStatus.KC_APPROVED, None]
)
def test_any_other_situation_lets_the_edit_through(status):
    refuse_edit_after_training(_Assignments(status), 1)
