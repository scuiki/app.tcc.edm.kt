"""get_existing_assignment: o assignment alvo, ou NotFound (o 404 do use case)."""

from __future__ import annotations

import pytest

from api.assignments.domain.assignment_entity import Assignment
from api.assignments.domain.existing_assignment import get_existing_assignment
from api.shared.domain.errors import NotFound


class _InMemoryAssignments:
    def __init__(self, *assignments: Assignment) -> None:
        self._by_id = {a.id: a for a in assignments}

    def get(self, assignment_id: int) -> Assignment | None:
        return self._by_id.get(assignment_id)


def test_returns_the_assignment_when_it_exists():
    assignment = Assignment(id=7, classroom_id=1, name="A", created_at="t0")

    assert get_existing_assignment(_InMemoryAssignments(assignment), 7) is assignment


def test_raises_not_found_when_it_does_not():
    with pytest.raises(NotFound):
        get_existing_assignment(_InMemoryAssignments(), 7)
