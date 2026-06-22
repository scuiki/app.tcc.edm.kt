"""Testes RED de contrato do router de dashboard (read-only) — DASH-01..05 + REC-01 + 999.2.

Espelham test_api_training.py: reusam o fixture api_client (TestClient sobre create_app() com
app.db migrado em tmp_path + DATA_ROOT hermético) e o helper _seed_assignment. Pinam o contrato
das rotas read-only do dashboard ANTES de o router existir/ser registrado — toda chamada cai em
404 (rota não-registrada) agora, que é o estado Wave 0 esperado (RED).

Contratos pinados:
  - moldura de incerteza (DASH-05/D-08): a resposta de mastery carrega first_auc E trained_at —
    nunca um veredito cru.
  - EDA sem modelo (DASH-04): o endpoint de EDA devolve 200 com agregados mesmo sem treino.
  - listagem de assignments (BACKLOG 999.2): id do DB + id ProgSnap2 + name + status.
  - 404 num id inteiro de assignment inexistente.
"""

from __future__ import annotations

from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos

_NOW = "2026-06-21T00:00:00Z"


def _seed_assignment(conn, status: str = "kc_approved", name: str = "Assignment 439") -> int:
    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name="Turma X", created_at=_NOW)
    )
    return repos.AssignmentRepository(conn).insert(
        models.Assignment(
            id=None,
            turma_id=turma_id,
            name=name,
            current_version_id=None,
            created_at=_NOW,
            status=status,
        )
    )


def test_uncertainty_frame(api_client):
    # DASH-05/D-08: a resposta de mastery NUNCA é um veredito cru — carrega first_auc + trained_at.
    client, conn = api_client
    aid = _seed_assignment(conn)

    resp = client.get(f"/dashboard/mastery/{aid}")
    assert resp.status_code == 200
    body = resp.json()
    # a moldura de incerteza está presente e nomeada como o contrato D-08 exige.
    assert "first_auc" in body
    assert "trained_at" in body
    # a matriz aluno×KC vem junto (DASH-01).
    assert "matrix" in body or "students" in body


def test_eda_without_model(api_client):
    # DASH-04: o EDA roda SEM modelo treinado — 200 com agregados do Parquet canônico.
    client, conn = api_client
    aid = _seed_assignment(conn, status="eda_only")  # sem treino, sem current_version_id

    resp = client.get(f"/dashboard/eda/{aid}")
    assert resp.status_code == 200
    body = resp.json()
    # os três agregados DASH-04 estão no payload.
    assert "success_rate" in body
    assert "learning_curve" in body
    assert "compile_error_rate" in body


def test_mastery_shape(api_client):
    # DASH-01/02/03: o payload de mastery traz a matriz + KCs críticos + alunos em atenção.
    client, conn = api_client
    aid = _seed_assignment(conn)

    body = client.get(f"/dashboard/mastery/{aid}").json()
    assert "critical_kcs" in body
    assert "at_risk_students" in body


def test_recommendations_shape(api_client):
    # REC-01: o endpoint de recomendações devolve uma lista rankeada (menor mastery primeiro).
    client, conn = api_client
    aid = _seed_assignment(conn)

    resp = client.get(f"/dashboard/recommendations/{aid}")
    assert resp.status_code == 200
    assert isinstance(resp.json()["recommendations"], list)


def test_list_assignments(api_client):
    # BACKLOG 999.2: GET /assignments expõe o id do DB + id ProgSnap2 + name + status, fechando
    # a ambiguidade de id-space (Pitfall 5) que forçava queries manuais no app.db na UAT da Fase 4.
    client, conn = api_client
    aid = _seed_assignment(conn, name="439")

    resp = client.get("/assignments")
    assert resp.status_code == 200
    items = resp.json()["assignments"]
    assert isinstance(items, list)
    row = next(a for a in items if a["id"] == aid)
    assert "id" in row            # id interno do DB (autoincrement)
    assert "progsnap_id" in row   # id ProgSnap2 (derivado do name, train.py:_progsnap_aid)
    assert "name" in row
    assert "status" in row


def test_mastery_unknown_assignment_404(api_client):
    # V5: id inteiro inexistente → 404 (nunca interpolar id como string em path/SQL).
    client, _ = api_client
    resp = client.get("/dashboard/mastery/999999")
    assert resp.status_code == 404


def test_eda_orphan_turma_404_not_500(api_client):
    # WR-01: um assignment cuja turma sumiu (linha removida sob um assignment órfão) fazia
    # turma.name explodir em AttributeError → 500 cru. A guarda devolve 404 limpo, não 500.
    client, conn = api_client
    aid = _seed_assignment(conn, status="eda_only")
    turma_id = repos.AssignmentRepository(conn).get(aid).turma_id
    # A FK assignment.turma_id→turma é enforced POR-CONEXÃO (PRAGMA foreign_keys=ON em db.py);
    # um assignment órfão surge quando uma conexão SEM enforcement removeu a turma. Reproduzimos
    # isso desligando o pragma só para o DELETE — o estado órfão que a guarda WR-01 cobre.
    conn.execute("PRAGMA foreign_keys=OFF;")
    conn.execute("DELETE FROM turma WHERE id = ?;", (turma_id,))
    conn.execute("PRAGMA foreign_keys=ON;")

    resp = client.get(f"/dashboard/eda/{aid}")
    assert resp.status_code == 404  # NÃO 500
