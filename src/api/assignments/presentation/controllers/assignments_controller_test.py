# GET /assignments expõe os dois ids de cada assignment, o do banco e o do dataset.

from __future__ import annotations

from api.assignments.domain.entities.assignment_entity import Assignment, AssignmentStatus
from api.classrooms.domain.entities.classroom_entity import Classroom
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.classrooms.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)


def _seed(conn, published_model_id=None) -> int:
    classroom_id = SqliteClassroomRepository(conn).add(
        Classroom(id=None, name="Turma X", created_at="t0")
    )
    return SqliteAssignmentRepository(conn).add(
        Assignment(
            id=None,
            classroom_id=classroom_id,
            name="Lista de laços",
            created_at="t0",
            status=AssignmentStatus.KC_APPROVED,
            progsnap_assignment_id=439,
            published_model_id=published_model_id,
        )
    )


def test_lists_every_assignment_with_both_ids(api_client):
    client, conn = api_client
    assignment_id = _seed(conn)

    response = client.get("/assignments")

    assert response.status_code == 200
    assert response.json() == {
        "assignments": [
            {
                "id": assignment_id,
                "progsnap_assignment_id": 439,  # da coluna própria, não derivado do nome
                "name": "Lista de laços",
                "status": "kc_approved",
                "published_model_id": None,
            }
        ]
    }


def test_an_empty_database_lists_nothing(api_client):
    client, _ = api_client

    assert client.get("/assignments").json() == {"assignments": []}
