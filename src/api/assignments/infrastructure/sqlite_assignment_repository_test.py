"""SqliteAssignmentRepository: ida e volta fiel, estados e o modelo publicado."""

from __future__ import annotations

import pytest

from api.assignments.domain.assignment_entity import Assignment, AssignmentStatus
from api.assignments.domain.classroom_entity import Classroom
from api.assignments.infrastructure.sqlite_assignment_repository import SqliteAssignmentRepository
from api.assignments.infrastructure.sqlite_classroom_repository import SqliteClassroomRepository


@pytest.fixture
def classroom_id(tmp_db) -> int:
    return SqliteClassroomRepository(tmp_db).add(Classroom(id=None, name="T", created_at="t0"))


def _assignment(classroom_id: int, **fields) -> Assignment:
    return Assignment(id=None, classroom_id=classroom_id, name="A439", created_at="t0", **fields)


def test_add_then_get_returns_the_same_assignment(tmp_db, classroom_id):
    repository = SqliteAssignmentRepository(tmp_db)
    new = _assignment(
        classroom_id, status=AssignmentStatus.KC_DRAFT, progsnap_assignment_id=439
    )

    assignment_id = repository.add(new)

    new.id = assignment_id
    assert repository.get(assignment_id) == new
    assert repository.get(999) is None


@pytest.mark.parametrize("status", list(AssignmentStatus))
def test_every_status_round_trips(tmp_db, classroom_id, status):
    repository = SqliteAssignmentRepository(tmp_db)

    assignment_id = repository.add(_assignment(classroom_id, status=status))

    assert repository.get(assignment_id).status is status


def test_set_status_moves_the_assignment_forward(tmp_db, classroom_id):
    repository = SqliteAssignmentRepository(tmp_db)
    assignment_id = repository.add(
        _assignment(classroom_id, status=AssignmentStatus.READY_FOR_KC_GENERATION)
    )

    repository.set_status(assignment_id, AssignmentStatus.KC_DRAFT)

    assert repository.get(assignment_id).status is AssignmentStatus.KC_DRAFT


def test_set_published_model_points_the_dashboard_at_a_version(tmp_db, classroom_id):
    repository = SqliteAssignmentRepository(tmp_db)
    assignment_id = repository.add(_assignment(classroom_id))
    model_id = tmp_db.execute(
        "INSERT INTO model_artifact (assignment_id, version_number, content_hash, artifact_dir, "
        "created_at) VALUES (?, 1, 'h', 'v1', 't0');",
        (assignment_id,),
    ).lastrowid

    repository.set_published_model(assignment_id, model_id)

    assert repository.get(assignment_id).published_model_id == model_id
