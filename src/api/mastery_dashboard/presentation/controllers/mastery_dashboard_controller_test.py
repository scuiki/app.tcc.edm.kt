# As rotas de /mastery-dashboard, formato das respostas, sem modelo e com assignment inexistente.

from __future__ import annotations

from api.assignments.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.domain.entities.classroom_entity import Classroom
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


def test_mastery_always_carries_the_trained_model_info(api_client):
    # a resposta de mastery nunca é um veredito cru, carrega first_auc + trained_at.
    client, conn = api_client
    aid = _seed_assignment(conn)

    resp = client.get(f"/mastery-dashboard/{aid}/mastery")
    assert resp.status_code == 200
    body = resp.json()
    # sem modelo publicado, o TrainedModelInfo vem vazio, mas vem
    assert body["first_attempt_auc"] is None and body["trained_at"] is None
    assert body["matrix"] == []


def test_pre_training_statistics_without_a_model(api_client):
    # as estatísticas pré-treino rodam sem modelo treinado, 200 com os agregados do dado limpo.
    client, conn = api_client
    aid = _seed_assignment(conn, status="statistics_only")  # sem treino, sem published_model_id

    resp = client.get(f"/mastery-dashboard/{aid}/pre-training-statistics")
    assert resp.status_code == 200
    body = resp.json()
    # os três agregados de estatísticas pré-treino estão no payload.
    assert "success_rate" in body
    assert "learning_curve" in body
    assert "compile_error_rate" in body


def test_mastery_shape(api_client):
    # o payload de mastery traz a matriz + KCs críticos + alunos em atenção.
    client, conn = api_client
    aid = _seed_assignment(conn)

    body = client.get(f"/mastery-dashboard/{aid}/mastery").json()
    assert "critical_kcs" in body
    assert "students_at_risk" in body


def test_recommendations_shape(api_client):
    # o endpoint de recomendações devolve uma lista rankeada (menor mastery primeiro).
    client, conn = api_client
    aid = _seed_assignment(conn)

    resp = client.get(f"/mastery-dashboard/{aid}/recommendations")
    assert resp.status_code == 200
    assert isinstance(resp.json()["recommendations"], list)


def test_mastery_unknown_assignment_404(api_client):
    # id inteiro inexistente → 404 (nunca interpolar id como string em path/SQL).
    client, _ = api_client
    resp = client.get("/mastery-dashboard/999999/mastery")
    assert resp.status_code == 404


def test_with_a_published_model_the_mastery_is_computed_and_ranked(
    api_client, trained_artifact, seed_cleaned_submissions
):
    # Caminho completo com um modelo de verdade (mínimo), a matriz, os KCs críticos e o AUC juntos.
    client, _ = api_client
    seed_cleaned_submissions()

    body = client.get(f"/mastery-dashboard/{trained_artifact.assignment_id}/mastery").json()
    recommendations = client.get(
        f"/mastery-dashboard/{trained_artifact.assignment_id}/recommendations"
    ).json()["recommendations"]

    assert body["trained_at"] is not None
    assert body["matrix"] and {"student_id", "kc_id", "mastery"} <= set(body["matrix"][0])
    means = [kc["mean_mastery"] for kc in body["critical_kcs"]]
    assert means == sorted(means)
    assert [r["kc_name"] for r in recommendations] and recommendations[0]["text"]
