"""Testes HTTP do router de treino (MODEL-01/02) — dispatch retorna na hora, GET faz poll.

Cobrem o contrato de borda: POST /training dispara o subprocess e devolve job_id 202 SEM
bloquear (Popen monkeypatchado — nenhum processo real nasce, args list-form sem shell
assertados), rejeita not-trainable/busy com 409, e GET /training/{job_id} devolve o progresso
da linha sob WAL / 404. Herméticos via api_client (tmp app.db); o assignment trainable é semeado
pela conexão de teste. NUNCA spawna treino real.
"""

from __future__ import annotations

import subprocess

import os
import sys

from edmkt_app.api import training
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos

_NOW = "2026-06-21T00:00:00Z"


# KC-03: o guard de /training agora exige 'kc_approved' (era 'trainable'). O caminho-feliz
# semeia já-aprovado; os testes de rejeição passam um status explícito não-aprovado.
def _seed_assignment(conn, status: str = "kc_approved") -> int:
    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name="Turma X", created_at=_NOW)
    )
    return repos.AssignmentRepository(conn).insert(
        models.Assignment(
            id=None,
            turma_id=turma_id,
            name="Assignment 439",
            progsnap_assignment_id=439,
            current_version_id=None,
            created_at=_NOW,
            status=status,
        )
    )


class _FakePopen:
    """Captura os args do dispatch sem spawnar processo (treino real nunca roda no teste)."""

    calls: list[list[str]] = []

    def __init__(self, args, *a, **kw):
        type(self).calls.append(args)


def test_dispatch_returns_job_id_immediately(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)

    resp = client.post("/training", json={"assignment_id": aid})

    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert isinstance(job_id, int)
    # Exatamente um dispatch, list-form, sys.executable + -m edmkt_app.train, ids como str.
    assert len(_FakePopen.calls) == 1
    args = _FakePopen.calls[0]
    assert args == [
        sys.executable,
        "-m",
        "edmkt_app.train",
        "--assignment",
        str(aid),
        "--job-id",
        str(job_id),
    ]
    # Nenhum shell=True / string interpolada (T-04-CMD): os args são uma lista de str puras.
    assert all(isinstance(a, str) for a in args)


def test_dispatch_rejects_not_trainable_409(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn, status="statistics_only")
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)

    resp = client.post("/training", json={"assignment_id": aid})
    assert resp.status_code == 409


def test_dispatch_blocked_before_approval_then_ok_after(api_client, monkeypatch):
    # KC-03: o gate humano — kc_draft (não-aprovado) é 409; aprovar destrava o /training.
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)

    assert client.post("/training", json={"assignment_id": aid}).status_code == 409

    repos.AssignmentRepository(conn).set_status(aid, "kc_approved")
    assert client.post("/training", json={"assignment_id": aid}).status_code == 202


def test_dispatch_rejects_missing_assignment_409(api_client, monkeypatch):
    client, _ = api_client
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    resp = client.post("/training", json={"assignment_id": 9999})
    assert resp.status_code == 409


def test_dispatch_rejects_busy_pipeline_409(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn)
    # Trava tomada por um PID VIVO (o próprio processo de teste) ⇒ pré-check rejeita 409.
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='training', acquired_at=? WHERE id=1;",
        (os.getpid(), _NOW),
    )
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)

    resp = client.post("/training", json={"assignment_id": aid})
    assert resp.status_code == 409


def test_poll_returns_progress_fields(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    job_id = client.post("/training", json={"assignment_id": aid}).json()["job_id"]

    # Simula o subprocess escrevendo progresso por-época sob WAL (conexão de teste separada).
    job_repo = repos.TrainingJobRepository(conn)
    job_repo.mark_running(job_id, total_epochs=40, started_at=_NOW)
    # O progresso corrente é DERIVADO da série append-only (0008), não de um campo mutável.
    repos.TrainingMetricRepository(conn).append(job_id, epoch=7, train_loss=0.42, recorded_at=_NOW)

    resp = client.get(f"/training/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["status"] == "running"
    assert body["current_epoch"] == 7
    assert body["total_epochs"] == 40
    assert body["train_loss"] == 0.42


def test_poll_returns_parse_rate(api_client, monkeypatch):
    """GET /training/{job_id} expõe parse_rate ao professor (SC-3) com o valor gravado."""
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    job_id = client.post("/training", json={"assignment_id": aid}).json()["job_id"]

    # Simula o subprocess concluindo com a taxa de parse gravada (conexão de teste separada).
    repos.TrainingJobRepository(conn).mark_done(job_id, updated_at=_NOW, parse_rate=0.86)

    resp = client.get(f"/training/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["parse_rate"] == 0.86


def test_poll_parse_rate_null_when_unset(api_client, monkeypatch):
    """Job ainda em andamento (sem parse_rate gravado) → GET devolve parse_rate null sem erro."""
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    job_id = client.post("/training", json={"assignment_id": aid}).json()["job_id"]

    resp = client.get(f"/training/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["parse_rate"] is None


def test_poll_missing_job_404(api_client):
    client, _ = api_client
    resp = client.get("/training/9999")
    assert resp.status_code == 404
