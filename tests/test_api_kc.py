"""RED — router /kc: dispatch+poll do job + edição da Q-matrix + gate de aprovação (KC-01/02/03).

Espelha test_api_training.py: `_FakePopen` captura os args do dispatch sem spawnar processo
(KC-gen real nunca roda no teste — T-05-01), assertando list-form `python -m
edmkt_app.kc_pipeline --assignment .. --job-id ..` SEM shell. Cobre: POST /kc/generate (202 +
job_id), GET /kc/jobs/{id} (poll/404), edição (rename/add/remove/merge com união de bindings),
a guarda 0-KC que faz ROLLBACK (D-07), POST /kc/approve → status kc_approved (KC-03), e a
reversão kc_approved→kc_draft ao editar após aprovar (D-06).

Wave 0: `edmkt_app.api.kc` ainda não existe → FALHA RED (gate da Wave 3).
"""

from __future__ import annotations

import sys

# RED: o router /kc ainda não existe (gate da Wave 3).
from edmkt_app.api import kc  # noqa: E402
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos

_NOW = "2026-06-21T00:00:00Z"


def _seed_assignment(conn, status: str = "trainable") -> int:
    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name="Turma X", created_at=_NOW)
    )
    return repos.AssignmentRepository(conn).insert(
        models.Assignment(
            id=None,
            turma_id=turma_id,
            name="Assignment 439",
            current_version_id=None,
            created_at=_NOW,
            status=status,
        )
    )


def _seed_kc(conn, assignment_id, name, kc_index=None) -> int:
    return repos.KCRepository(conn).insert(
        models.KC(id=None, assignment_id=assignment_id, name=name, kc_index=kc_index)
    )


def _bind(conn, assignment_id, kc_id, problem_id) -> None:
    repos.QMatrixRepository(conn).insert(
        models.QMatrix(id=None, assignment_id=assignment_id, kc_id=kc_id, problem_id=problem_id)
    )


class _FakePopen:
    """Captura os args do dispatch sem spawnar processo (KC-gen real nunca roda)."""

    calls: list[list[str]] = []

    def __init__(self, args, *a, **kw):
        type(self).calls.append(args)


# --- dispatch + poll (espelha test_api_training) ----------------------------------


def test_generate_dispatches_list_form_and_returns_job_id(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(kc.subprocess, "Popen", _FakePopen)

    resp = client.post("/kc/generate", json={"assignment_id": aid})

    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert isinstance(job_id, int)
    assert len(_FakePopen.calls) == 1
    args = _FakePopen.calls[0]
    assert args == [
        sys.executable,
        "-m",
        "edmkt_app.kc_pipeline",
        "--assignment",
        str(aid),
        "--job-id",
        str(job_id),
    ]
    assert all(isinstance(a, str) for a in args)  # sem shell / sem interpolação (T-05-02)


def test_poll_returns_job_fields(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(kc.subprocess, "Popen", _FakePopen)
    job_id = client.post("/kc/generate", json={"assignment_id": aid}).json()["job_id"]

    # Simula o subprocess marcando running + estágio sob WAL (conexão de teste separada).
    job_repo = repos.KCJobRepository(conn)
    job_repo.mark_running(job_id, started_at=_NOW)
    job_repo.update_stage(job_id, stage="cluster", updated_at=_NOW)

    resp = client.get(f"/kc/jobs/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["status"] == "running"
    assert body["stage"] == "cluster"


def test_poll_missing_job_404(api_client):
    client, _ = api_client
    assert client.get("/kc/jobs/9999").status_code == 404


# --- edição da Q-matrix (KC-02, D-07) ---------------------------------------------


def test_rename_kc_updates_name(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    kc_id = _seed_kc(conn, aid, "nome antigo")
    _bind(conn, aid, kc_id, problem_id=1)

    resp = client.patch(f"/kc/{kc_id}", json={"name": "nome novo"})
    assert resp.status_code == 200

    assert repos.KCRepository(conn).get(kc_id).name == "nome novo"


def test_merge_unions_bindings(api_client):
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    keep = _seed_kc(conn, aid, "keep")
    drop = _seed_kc(conn, aid, "drop")
    _bind(conn, aid, keep, problem_id=1)
    _bind(conn, aid, drop, problem_id=2)  # binding distinto migra para keep

    resp = client.post("/kc/merge", json={"assignment_id": aid, "kc_keep": keep, "kc_drop": drop})
    assert resp.status_code == 200

    # União: keep agora cobre os problemas 1 e 2; drop sumiu.
    problems = {
        r["problem_id"]
        for r in conn.execute(
            "SELECT problem_id FROM qmatrix WHERE kc_id=?;", (keep,)
        ).fetchall()
    }
    assert problems == {1, 2}
    assert repos.KCRepository(conn).get(drop) is None


def test_remove_that_empties_a_problem_is_blocked(api_client):
    # D-07: remover o único KC de um problema o deixaria com 0 KCs → BLOQUEADO + ROLLBACK.
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    only_kc = _seed_kc(conn, aid, "único")
    _bind(conn, aid, only_kc, problem_id=1)

    resp = client.delete(f"/kc/{only_kc}")
    assert resp.status_code >= 400  # rejeitado

    # ROLLBACK: o KC e seu binding continuam intactos.
    assert repos.KCRepository(conn).get(only_kc) is not None
    assert conn.execute("SELECT COUNT(*) FROM qmatrix WHERE kc_id=?;", (only_kc,)).fetchone()[0] == 1


# --- gate de aprovação (KC-03, D-06) ----------------------------------------------


def test_approve_sets_kc_approved(api_client):
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    kc_id = _seed_kc(conn, aid, "x")
    _bind(conn, aid, kc_id, problem_id=1)

    resp = client.post("/kc/approve", json={"assignment_id": aid})
    assert resp.status_code == 200

    assert repos.AssignmentRepository(conn).get(aid).status == "kc_approved"


def test_editing_after_approval_reverts_status(api_client):
    # D-06: editar um KC após aprovar reverte kc_approved → kc_draft (re-aprovação necessária).
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_approved")
    a = _seed_kc(conn, aid, "a")
    b = _seed_kc(conn, aid, "b")
    _bind(conn, aid, a, problem_id=1)
    _bind(conn, aid, b, problem_id=1)  # problema 1 tem 2 KCs (remover 1 não o zera)

    resp = client.patch(f"/kc/{a}", json={"name": "a-editado"})
    assert resp.status_code == 200

    assert repos.AssignmentRepository(conn).get(aid).status == "kc_draft"
