# As três rotas de leitura, os problemas, os KCs e os KCs de cada problema.

from __future__ import annotations

from tests.fixtures.knowledge_components import add_extraction
from tests.fixtures.problems import add_problems


def _seed(trained_artifact):
    # O trained_artifact liga Laços aos problemas 1 e 3 e Condicionais aos 2 e 3; o 4 fica sem KC
    add_problems(trained_artifact.conn, trained_artifact.assignment_id, [4])
    trained_artifact.conn.execute(
        "UPDATE problem SET description = 'Soma os elementos', "
        "statement = 'Devolva a soma dos elementos do vetor.' "
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
    # O problema 4 só tem execuções incorretas
    add_extraction(
        trained_artifact.conn,
        assignment_id,
        correct_runs={1: 3, 2: 1, 3: 2},
        incorrect_runs={1: 2, 4: 1},
        extracted_at="2026-10-07T02:30:00Z",
    )

    body = client.get(f"/assignments/{assignment_id}/problems/knowledge-components").json()

    assert body["status"] == "kc_approved"
    assert body["extracted_at"] == "2026-10-07T02:30:00Z"
    assert [
        (
            p["problem_id"],
            p["description"],
            p["statement"],
            p["correct_run_count"],
            [kc["name"] for kc in p["knowledge_components"]],
        )
        for p in body["problems"]
    ] == [
        (1, "Soma os elementos", "Devolva a soma dos elementos do vetor.", 3, ["Laços"]),
        (2, None, None, 1, ["Condicionais"]),
        (3, None, None, 2, ["Laços", "Condicionais"]),
        (4, None, None, 0, []),
    ]


def test_problem_kcs_route_without_runs_or_a_done_job_counts_zero_and_has_no_extraction_date(
    api_client, trained_artifact
):
    client, _ = api_client
    assignment_id = _seed(trained_artifact)

    body = client.get(f"/assignments/{assignment_id}/problems/knowledge-components").json()

    assert body["extracted_at"] is None
    assert [(p["problem_id"], p["correct_run_count"]) for p in body["problems"]] == [
        (1, 0),
        (2, 0),
        (3, 0),
        (4, 0),
    ]


def test_the_three_routes_answer_404_for_a_missing_assignment(api_client):
    client, _ = api_client

    for path in ("/assignments/999/problems", "/assignments/999/problems/knowledge-components"):
        assert client.get(path).status_code == 404
    assert client.get("/knowledge-components", params={"assignment_id": 999}).status_code == 404
