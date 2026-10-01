# As rotas de /mastery-dashboard, formato das respostas, sem modelo e com assignment inexistente.

from __future__ import annotations

import json
from pathlib import Path

from api.classrooms.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.classrooms.domain.entities.classroom_entity import Classroom
from api.assignments.domain.entities.assignment_entity import Assignment

_NOW = "2026-06-21T00:00:00Z"


def _seed_assignment(
    conn, status: str = "kc_approved", name: str = "Assignment 439", progsnap_id: int = 439
) -> int:
    classroom_id = SqliteClassroomRepository(conn).add(
        Classroom(id=None, name="Turma X", created_at=_NOW)
    )
    return SqliteAssignmentRepository(conn).add(
        Assignment(
            id=None,
            classroom_id=classroom_id,
            name=name,
            published_model_id=None,
            created_at=_NOW,
            status=status,
            progsnap_assignment_id=progsnap_id,
        )
    )


# O que aconteceu, desde a importação


def test_submission_statistics_without_data_are_empty_not_an_error(api_client):
    # o bloco "o que aconteceu" existe desde a importação, sem modelo; sem dado, listas vazias.
    client, conn = api_client
    aid = _seed_assignment(conn, status="statistics_only")

    resp = client.get(f"/mastery-dashboard/{aid}/submission-statistics")

    assert resp.status_code == 200
    assert resp.json() == {
        "assignment_id": aid, "student_count": 0, "problems": [], "knowledge_components": []
    }


def test_submission_statistics_count_the_seeded_runs(
    api_client, trained_artifact, seed_cleaned_submissions
):
    # 3 alunos, cada um erra e depois acerta o 1, acerta o 2 de primeira, erra o 3; 1 CE no 1.
    client, _ = api_client
    seed_cleaned_submissions(with_compile_errors=True)

    body = client.get(
        f"/mastery-dashboard/{trained_artifact.assignment_id}/submission-statistics"
    ).json()

    assert body["student_count"] == 3
    by_id = {p["problem_id"]: p for p in body["problems"]}
    assert [p["problem_id"] for p in body["problems"]] == [3, 1, 2]  # da menor taxa para a maior
    assert by_id[1]["success_rate"] == 0.5 and by_id[1]["median_attempts_to_complete"] == 2.0
    assert by_id[1]["students_completed"] == 3 and by_id[1]["compile_errors_per_run"] == 0.5
    assert by_id[3]["students_completed"] == 0 and by_id[3]["median_attempts_to_complete"] is None
    # o problema 3 exige os dois conceitos do trained_artifact, com nome
    assert sorted(k["kc_name"] for k in by_id[3]["kcs"]) == ["Condicionais", "Laços"]
    # Laços cobre 1 e 3 (3 acertos em 9 execuções); Condicionais cobre 2 e 3 (3 em 6)
    assert [k["kc_name"] for k in body["knowledge_components"]] == ["Laços", "Condicionais"]


def test_submission_statistics_hide_concepts_until_they_are_approved(
    api_client, trained_artifact, seed_cleaned_submissions
):
    client, conn = api_client
    seed_cleaned_submissions()
    SqliteAssignmentRepository(conn).set_status(trained_artifact.assignment_id, "kc_draft")

    body = client.get(
        f"/mastery-dashboard/{trained_artifact.assignment_id}/submission-statistics"
    ).json()

    assert body["knowledge_components"] == [] and all(p["kcs"] == [] for p in body["problems"])


# O que o modelo prevê, só com modelo publicado


def test_without_a_published_model_the_mastery_is_empty_and_says_so(api_client):
    client, conn = api_client
    aid = _seed_assignment(conn)

    mastery = client.get(f"/mastery-dashboard/{aid}/mastery")
    students = client.get(f"/mastery-dashboard/{aid}/students")

    assert mastery.status_code == 200
    assert mastery.json() == {
        "assignment_id": aid, "model": None, "knowledge_components": [], "problems": []
    }
    assert students.json() == {"assignment_id": aid, "students": []}
    assert client.get(f"/mastery-dashboard/{aid}/students/Sa").status_code == 404


def test_unknown_assignment_is_404(api_client):
    # id inteiro inexistente → 404 (nunca interpolar id como string em path/SQL).
    client, _ = api_client

    assert client.get("/mastery-dashboard/999999/mastery").status_code == 404
    assert client.get("/mastery-dashboard/999999/submission-statistics").status_code == 404
    assert client.get("/mastery-dashboard/999999/students").status_code == 404


def test_with_a_published_model_the_mastery_comes_by_concept_and_by_problem(
    api_client, trained_artifact, seed_cleaned_submissions
):
    # Caminho completo com um modelo de verdade (mínimo), 3 alunos, 3 problemas, 2 conceitos.
    client, _ = api_client
    seed_cleaned_submissions()

    body = client.get(f"/mastery-dashboard/{trained_artifact.assignment_id}/mastery").json()

    assert body["model"] == {
        "version_number": trained_artifact.version_number,
        "trained_at": trained_artifact.trained_model.created_at,
        "student_count": 3, "problem_count": 3, "knowledge_component_count": 2,
    }
    by_name = {kc["kc_name"]: kc for kc in body["knowledge_components"]}
    assert by_name["Laços"]["problem_ids"] == [1, 3] and by_name["Condicionais"]["problem_ids"] == [2, 3]
    means = [kc["mean_mastery"] for kc in body["knowledge_components"]]
    assert means == sorted(means) and all(0.0 <= m <= 1.0 for m in means)
    assert all(sum(kc["histogram"]) == 3 and len(kc["histogram"]) == 10 for kc in body["knowledge_components"])
    assert [p["problem_id"] for p in sorted(body["problems"], key=lambda p: p["problem_id"])] == [1, 2, 3]
    three = next(p for p in body["problems"] if p["problem_id"] == 3)
    assert sorted(k["kc_name"] for k in three["kcs"]) == ["Condicionais", "Laços"]
    assert sum(three["histogram"]) == 3


def _strip_format_version(trained_artifact) -> None:
    config = Path(trained_artifact.artifact_dir) / "config.json"
    meta = json.loads(config.read_text())
    del meta["format_version"]
    config.write_text(json.dumps(meta))


def test_a_model_of_an_old_format_is_409_with_a_clear_message(
    api_client, trained_artifact, seed_cleaned_submissions
):
    client, _ = api_client
    seed_cleaned_submissions()
    _strip_format_version(trained_artifact)

    resp = client.get(f"/mastery-dashboard/{trained_artifact.assignment_id}/mastery")

    assert resp.status_code == 409
    assert "formato" in resp.json()["detail"]


def test_the_stored_mastery_of_an_old_model_keeps_serving(
    api_client, trained_artifact, seed_cleaned_submissions
):
    # A matriz gravada não recarrega o modelo, então o painel de um modelo antigo continua
    client, _ = api_client
    seed_cleaned_submissions()
    url = f"/mastery-dashboard/{trained_artifact.assignment_id}/mastery"
    first = client.get(url)
    _strip_format_version(trained_artifact)

    again = client.get(url)

    assert first.status_code == again.status_code == 200
    assert again.json() == first.json()


def test_students_come_with_what_they_did_and_their_weakest_concepts(
    api_client, trained_artifact, seed_cleaned_submissions
):
    client, _ = api_client
    seed_cleaned_submissions()

    body = client.get(f"/mastery-dashboard/{trained_artifact.assignment_id}/students").json()

    assert sorted(s["student_id"] for s in body["students"]) == ["Sa", "Sb", "Sc"]
    means = [s["mean_mastery"] for s in body["students"]]
    assert means == sorted(means)
    for student in body["students"]:
        # cada aluno completou os problemas 1 e 2 e tentou o 3; só há dois conceitos para listar
        assert (student["completed"], student["attempted"]) == (2, 3)
        assert [kc["kc_name"] for kc in student["weakest_kcs"]] and len(student["weakest_kcs"]) == 2
        masteries = [kc["mastery"] for kc in student["weakest_kcs"]]
        assert masteries == sorted(masteries)


def test_the_student_detail_has_every_concept_and_every_problem(
    api_client, trained_artifact, seed_cleaned_submissions
):
    client, _ = api_client
    seed_cleaned_submissions(with_compile_errors=True)

    resp = client.get(f"/mastery-dashboard/{trained_artifact.assignment_id}/students/Sb")

    assert resp.status_code == 200
    body = resp.json()
    assert body["student_id"] == "Sb"
    assert (body["completed"], body["attempted"], body["runs"], body["compile_errors"]) == (2, 3, 4, 1)
    assert sorted(kc["kc_name"] for kc in body["knowledge_components"]) == ["Condicionais", "Laços"]
    assert sorted(p["problem_id"] for p in body["problems"]) == [1, 2, 3]
    assert 0.0 <= body["mean_mastery"] <= 1.0
    assert client.get(
        f"/mastery-dashboard/{trained_artifact.assignment_id}/students/ninguem"
    ).status_code == 404
