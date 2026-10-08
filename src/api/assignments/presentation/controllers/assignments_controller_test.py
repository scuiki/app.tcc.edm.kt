# GET /assignments expõe os dois ids de cada assignment, o do banco e o do dataset.

from __future__ import annotations

from tests.fixtures.assignments import add_assignment
from tests.fixtures.classrooms import add_classroom


def test_lists_every_assignment_with_both_ids(api_client):
    client, conn = api_client
    assignment_id = add_assignment(
        conn,
        add_classroom(conn),
        name="Lista de laços",
        status="kc_approved",
        progsnap_assignment_id=439,
    )

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
