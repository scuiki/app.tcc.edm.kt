# As três rotas de leitura, os problemas, os KCs e os KCs de cada problema.

from __future__ import annotations

from tests.fixtures.problems import add_problems


def _seed(trained_artifact):
    # O trained_artifact liga Laços aos problemas 1 e 3 e Condicionais aos 2 e 3; o 4 fica sem KC
    add_problems(trained_artifact.conn, trained_artifact.assignment_id, [4])
    trained_artifact.conn.execute(
        "UPDATE problem SET description = 'Soma os elementos' "
        "WHERE assignment_id = ? AND problem_id = 1;",
        (trained_artifact.assignment_id,),
    )
    return trained_artifact.assignment_id


def test_the_problems_route_lists_every_problem_with_its_description(api_client, trained_artifact):
    client, _ = api_client
    assignment_id = _seed(trained_artifact)

    body = client.get(f"/assignments/{assignment_id}/problems").json()

    assert body == {
        "assignment_id": assignment_id,
        "problems": [
            {"problem_id": 1, "description": "Soma os elementos"},
            {"problem_id": 2, "description": None},
            {"problem_id": 3, "description": None},
            {"problem_id": 4, "description": None},
        ],
    }


def test_the_knowledge_components_route_lists_each_kc_with_its_problems(
    api_client, trained_artifact
):
    client, _ = api_client
    assignment_id = _seed(trained_artifact)

    body = client.get("/knowledge-components", params={"assignment_id": assignment_id}).json()

    assert [(kc["name"], kc["problem_ids"]) for kc in body["knowledge_components"]] == [
        ("Laços", [1, 3]),
        ("Condicionais", [2, 3]),
    ]


def test_problem_kcs_route_joins_problems_and_kcs_including_problems_without_kc(
    api_client, trained_artifact
):
    client, _ = api_client
    assignment_id = _seed(trained_artifact)

    body = client.get(f"/assignments/{assignment_id}/problems/knowledge-components").json()

    assert body["status"] == "kc_approved"
    assert [
        (p["problem_id"], p["description"], [kc["name"] for kc in p["knowledge_components"]])
        for p in body["problems"]
    ] == [
        (1, "Soma os elementos", ["Laços"]),
        (2, None, ["Condicionais"]),
        (3, None, ["Laços", "Condicionais"]),
        (4, None, []),
    ]


def test_the_three_routes_answer_404_for_a_missing_assignment(api_client):
    client, _ = api_client

    for path in ("/assignments/999/problems", "/assignments/999/problems/knowledge-components"):
        assert client.get(path).status_code == 404
    assert client.get("/knowledge-components", params={"assignment_id": 999}).status_code == 404
