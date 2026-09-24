# O CRUD de /classrooms, a regra do nome único, o soft delete e a listagem com as contagens.

from __future__ import annotations

from tests.fixtures.problems import add_problems


def _create(client, name: str) -> dict:
    resp = client.post("/classrooms", json={"name": name})
    assert resp.status_code == 201
    return resp.json()


def _add_assignment(conn, classroom_id: int, published_model_id=None) -> int:
    return conn.execute(
        "INSERT INTO assignment (classroom_id, name, created_at, published_model_id) "
        "VALUES (?, 'A', 't0', ?);",
        (classroom_id, published_model_id),
    ).lastrowid


def _add_submission(conn, assignment_id: int, student_id: str, problem_id: int) -> None:
    conn.execute(
        "INSERT INTO submission (assignment_id, student_id, problem_id, submitted_at, event_type, "
        "is_correct) VALUES (?, ?, ?, 't0', 'Run.Program', 1);",
        (assignment_id, student_id, problem_id),
    )


def test_a_classroom_is_created_with_only_a_name(api_client):
    client, _ = api_client

    created = _create(client, "  Turma 6  ")

    assert created["name"] == "Turma 6"  # sem os espaços das pontas
    assert created["id"] > 0 and created["created_at"]


def test_a_name_already_used_by_an_active_classroom_is_refused(api_client):
    client, _ = api_client
    _create(client, "Turma 6")

    assert client.post("/classrooms", json={"name": "turma  6"}).status_code == 409
    assert client.post("/classrooms", json={"name": "   "}).status_code == 422


def test_renaming_keeps_the_same_rule_and_allows_another_spelling_of_its_own_name(api_client):
    client, _ = api_client
    first, second = _create(client, "Turma A"), _create(client, "Turma B")

    assert client.put(f"/classrooms/{first['id']}", json={"name": "turma a"}).status_code == 200
    assert client.put(f"/classrooms/{first['id']}", json={"name": "Turma B"}).status_code == 409
    renamed = client.put(f"/classrooms/{second['id']}", json={"name": "Turma C"}).json()
    assert renamed["name"] == "Turma C"
    assert client.put("/classrooms/999", json={"name": "X"}).status_code == 404


def test_removing_a_classroom_hides_it_and_its_assignments_but_keeps_the_rows(api_client):
    client, conn = api_client
    classroom = _create(client, "Turma 6")
    assignment_id = _add_assignment(conn, classroom["id"])

    resp = client.delete(f"/classrooms/{classroom['id']}")

    assert resp.json() == {"deleted_classroom_id": classroom["id"]}
    assert client.get("/classrooms").json()["classrooms"] == []
    assert client.get("/assignments").json()["assignments"] == []
    assert client.get(f"/assignments/{assignment_id}/problems").status_code == 404
    kept = conn.execute("SELECT COUNT(*) FROM assignment WHERE deleted_at IS NOT NULL;").fetchone()
    assert kept[0] == 1  # soft delete, a linha continua lá
    assert client.post("/classrooms", json={"name": "Turma 6"}).status_code == 201  # nome livre
    assert client.delete(f"/classrooms/{classroom['id']}").status_code == 404


def test_the_list_counts_problems_and_distinct_students_and_derives_the_status(api_client):
    client, conn = api_client
    empty = _create(client, "Vazia")
    started = _create(client, "Com dados")
    trained = _create(client, "Treinada")
    first = _add_assignment(conn, started["id"])
    second = _add_assignment(conn, started["id"])
    add_problems(conn, first, [1, 2])
    add_problems(conn, second, [1])
    _add_submission(conn, first, "S1", 1)
    _add_submission(conn, second, "S1", 1)  # o mesmo aluno em dois assignments conta uma vez
    _add_submission(conn, second, "S2", 1)
    trained_assignment = _add_assignment(conn, trained["id"])
    add_problems(conn, trained_assignment, [5])
    model_id = conn.execute(
        "INSERT INTO model_artifact (assignment_id, version_number, content_hash, artifact_dir, "
        "created_at) VALUES (?, 1, 'h', 'd', 't0');",
        (trained_assignment,),
    ).lastrowid
    conn.execute(
        "UPDATE assignment SET published_model_id = ? WHERE id = ?;", (model_id, trained_assignment)
    )

    body = {c["name"]: c for c in client.get("/classrooms").json()["classrooms"]}

    assert (body["Vazia"]["problem_count"], body["Vazia"]["status"]) == (0, "awaiting_data")
    assert body["Com dados"]["problem_count"] == 3
    assert body["Com dados"]["student_count"] == 2
    assert body["Com dados"]["status"] == "in_progress"
    assert body["Treinada"]["status"] == "trained"


def test_assignments_can_be_listed_for_one_classroom(api_client):
    client, conn = api_client
    mine, other = _create(client, "Minha"), _create(client, "Outra")
    wanted = _add_assignment(conn, mine["id"])
    _add_assignment(conn, other["id"])

    body = client.get("/assignments", params={"classroom_id": mine["id"]}).json()

    assert [a["id"] for a in body["assignments"]] == [wanted]
