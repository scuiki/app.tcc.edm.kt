# Rotas de /knowledge-components, disparo/progresso da geração, edição e aprovação da Q-matrix.
from __future__ import annotations

import subprocess
import sys

from api.assignments.domain.entities.assignment_entity import Assignment
from api.classrooms.domain.entities.classroom_entity import Classroom
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.classrooms.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.entities.qmatrix_binding_entity import QMatrixBinding
from api.knowledge_components.infrastructure.repositories.sqlite_kc_generation_job_repository import (
    SqliteKnowledgeComponentGenerationJobRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_qmatrix_repository import (
    SqliteQMatrixRepository,
)
from api.knowledge_components.presentation.dependencies import KC_GENERATION_WORKER

_NOW = "2026-06-21T00:00:00Z"


def _seed_assignment(conn, status: str = "ready_for_kc_generation") -> int:
    classroom_id = SqliteClassroomRepository(conn).add(
        Classroom(id=None, name="Turma X", created_at=_NOW)
    )
    return SqliteAssignmentRepository(conn).add(
        Assignment(
            id=None,
            classroom_id=classroom_id,
            name="Assignment 439",
            progsnap_assignment_id=439,
            published_model_id=None,
            created_at=_NOW,
            status=status,
        )
    )


def _seed_kc(conn, assignment_id, name, kc_index=None) -> int:
    return SqliteKnowledgeComponentRepository(conn).add(
        KnowledgeComponent(id=None, assignment_id=assignment_id, name=name, group_index=kc_index)
    )


def _bind(conn, assignment_id, kc_id, problem_id) -> None:
    SqliteQMatrixRepository(conn).add(
        QMatrixBinding(id=None, assignment_id=assignment_id, kc_id=kc_id, problem_id=problem_id)
    )


# Captura os args do dispatch sem spawnar processo, KC-gen real nunca roda.
class _FakePopen:
    calls: list[list[str]] = []

    def __init__(self, args, *a, **kw):
        type(self).calls.append(args)


# --- dispatch e poll ----------------------------------


def test_generate_dispatches_list_form_and_returns_job_id(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)

    resp = client.post("/knowledge-components/generation-jobs", json={"assignment_id": aid})

    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert isinstance(job_id, int)
    assert len(_FakePopen.calls) == 1
    args = _FakePopen.calls[0]
    assert args == [
        sys.executable,
        "-m",
        KC_GENERATION_WORKER,
        "--assignment",
        str(aid),
        "--job-id",
        str(job_id),
    ]
    assert all(isinstance(a, str) for a in args)  # sem shell / sem interpolação


def test_poll_returns_job_fields(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    job_id = client.post("/knowledge-components/generation-jobs", json={"assignment_id": aid}).json()["job_id"]

    # Simula o subprocess marcando running + estágio sob WAL (conexão de teste separada).
    job_repo = SqliteKnowledgeComponentGenerationJobRepository(conn)
    job_repo.mark_running(job_id, started_at=_NOW)
    job_repo.update_stage(job_id, stage="cluster", updated_at=_NOW)

    resp = client.get(f"/knowledge-components/generation-jobs/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["status"] == "running"
    assert body["stage"] == "cluster"


def test_poll_missing_job_404(api_client):
    client, _ = api_client
    assert client.get("/knowledge-components/generation-jobs/9999").status_code == 404


# --- edição da Q-matrix ---


def test_rename_kc_updates_name(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    kc_id = _seed_kc(conn, aid, "nome antigo")
    _bind(conn, aid, kc_id, problem_id=1)

    resp = client.patch(f"/knowledge-components/{kc_id}", json={"name": "nome novo"})
    assert resp.status_code == 200

    assert SqliteKnowledgeComponentRepository(conn).get(kc_id).name == "nome novo"


def test_merge_unions_bindings(api_client):
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    keep = _seed_kc(conn, aid, "keep")
    drop = _seed_kc(conn, aid, "drop")
    _bind(conn, aid, keep, problem_id=1)
    _bind(conn, aid, drop, problem_id=2)  # binding distinto migra para keep

    resp = client.post("/knowledge-components/merge", json={"assignment_id": aid, "keep_kc_id": keep, "drop_kc_id": drop})
    assert resp.status_code == 200

    # União, keep agora cobre os problemas 1 e 2; drop sumiu.
    problems = {
        r["problem_id"]
        for r in conn.execute(
            "SELECT problem_id FROM qmatrix WHERE kc_id=?;", (keep,)
        ).fetchall()
    }
    assert problems == {1, 2}
    assert SqliteKnowledgeComponentRepository(conn).get(drop) is None


def test_remove_that_empties_a_problem_is_blocked(api_client):
    # remover o único KC de um problema o deixaria com 0 KCs → BLOQUEADO + ROLLBACK.
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    only_kc = _seed_kc(conn, aid, "único")
    _bind(conn, aid, only_kc, problem_id=1)

    resp = client.delete(f"/knowledge-components/{only_kc}")
    assert resp.status_code >= 400  # rejeitado

    # ROLLBACK, o KC e seu binding continuam intactos.
    assert SqliteKnowledgeComponentRepository(conn).get(only_kc) is not None
    assert conn.execute("SELECT COUNT(*) FROM qmatrix WHERE kc_id=?;", (only_kc,)).fetchone()[0] == 1


def test_merge_rejects_cross_assignment_kc(api_client):
    # kc_drop pertence a OUTRO assignment → merge rejeitado (sem delete cross-assignment).
    client, conn = api_client
    aid_a = _seed_assignment(conn, status="kc_draft")
    aid_b = _seed_assignment(conn, status="kc_draft")
    keep = _seed_kc(conn, aid_a, "keep")
    _bind(conn, aid_a, keep, problem_id=1)
    # KC de OUTRO assignment, não pode ser tocado por um merge sobre aid_a.
    foreign = _seed_kc(conn, aid_b, "foreign")
    _bind(conn, aid_b, foreign, problem_id=1)

    resp = client.post(
        "/knowledge-components/merge", json={"assignment_id": aid_a, "keep_kc_id": keep, "drop_kc_id": foreign}
    )
    assert resp.status_code in (403, 409)

    # O KC alheio (e seu binding) seguem intactos, nenhuma FK pendurada.
    assert SqliteKnowledgeComponentRepository(conn).get(foreign) is not None
    assert (
        conn.execute("SELECT COUNT(*) FROM qmatrix WHERE kc_id=?;", (foreign,)).fetchone()[0] == 1
    )


def test_merge_rejects_keep_from_other_assignment(api_client):
    # keep_kc_id alheio também é rejeitado (qualquer um dos dois fora do assignment falha).
    client, conn = api_client
    aid_a = _seed_assignment(conn, status="kc_draft")
    aid_b = _seed_assignment(conn, status="kc_draft")
    drop = _seed_kc(conn, aid_a, "drop")
    _bind(conn, aid_a, drop, problem_id=1)
    foreign_keep = _seed_kc(conn, aid_b, "foreign-keep")

    resp = client.post(
        "/knowledge-components/merge", json={"assignment_id": aid_a, "keep_kc_id": foreign_keep, "drop_kc_id": drop}
    )
    assert resp.status_code in (403, 409)
    assert SqliteKnowledgeComponentRepository(conn).get(drop) is not None  # nada deletado


def test_merge_self_merge_rejected(api_client):
    # mesclar um KC consigo mesmo é uma operação sem sentido → 409 claro.
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    kc_id = _seed_kc(conn, aid, "x")
    _bind(conn, aid, kc_id, problem_id=1)

    resp = client.post("/knowledge-components/merge", json={"assignment_id": aid, "keep_kc_id": kc_id, "drop_kc_id": kc_id})
    assert resp.status_code == 409
    assert SqliteKnowledgeComponentRepository(conn).get(kc_id) is not None  # não se autodeletou


# --- gate de aprovação ---


def test_approve_sets_kc_approved(api_client):
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    kc_id = _seed_kc(conn, aid, "x")
    _bind(conn, aid, kc_id, problem_id=1)

    resp = client.post("/knowledge-components/approve-qmatrix", json={"assignment_id": aid})
    assert resp.status_code == 200

    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_approved"


def test_approve_rejects_non_draft_assignment(api_client):
    # Aprovar sem gerar KCs burlaria a revisão e treinaria sobre Q-matrix inexistente, é 409.
    client, conn = api_client
    aid = _seed_assignment(conn, status="ready_for_kc_generation")

    resp = client.post("/knowledge-components/approve-qmatrix", json={"assignment_id": aid})
    assert resp.status_code == 409
    assert SqliteAssignmentRepository(conn).get(aid).status == "ready_for_kc_generation"  # parado


def test_approve_rejects_draft_without_kcs(api_client):
    # kc_draft mas SEM nenhum KC não pode ser aprovado (não há Q-matrix a treinar).
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")  # nenhum KC inserido

    resp = client.post("/knowledge-components/approve-qmatrix", json={"assignment_id": aid})
    assert resp.status_code == 409
    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_draft"


def test_editing_after_approval_reverts_status(api_client):
    # editar um KC após aprovar reverte kc_approved → kc_draft (re-aprovação necessária).
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_approved")
    a = _seed_kc(conn, aid, "a")
    b = _seed_kc(conn, aid, "b")
    _bind(conn, aid, a, problem_id=1)
    _bind(conn, aid, b, problem_id=1)  # problema 1 tem 2 KCs (remover 1 não o zera)

    resp = client.patch(f"/knowledge-components/{a}", json={"name": "a-editado"})
    assert resp.status_code == 200

    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_draft"
