"""As rotas de /training-jobs: o disparo devolve o job na hora, o GET acompanha o progresso.

O Popen é substituído: nenhum processo real nasce, e os argumentos (list-form, sem shell) são
conferidos. Cobre a recusa sem Q-matrix aprovada ou com outro job rodando (409), o progresso lido
da curva de loss, a taxa de parse e a curva completa. Herméticos via api_client.
"""

from __future__ import annotations

import os
import subprocess
import sys

from api.assignments.domain.entities.assignment_entity import Assignment
from api.assignments.domain.entities.classroom_entity import Classroom
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.model_training.domain.entities.training_epoch_metric import TrainingEpochMetric
from api.model_training.infrastructure.repositories.sqlite_training_epoch_metric_repository import (
    SqliteTrainingEpochMetricRepository,
)
from api.model_training.infrastructure.repositories.sqlite_training_job_repository import (
    SqliteTrainingJobRepository,
)
from api.model_training.presentation.dependencies import TRAINING_WORKER

_NOW = "2026-06-21T00:00:00Z"


# O treino exige a Q-matrix aprovada: o caminho feliz semeia kc_approved; as recusas passam outro.
def _seed_assignment(conn, status: str = "kc_approved") -> int:
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

    resp = client.post("/training-jobs", json={"assignment_id": aid})

    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert isinstance(job_id, int)
    # Exatamente um disparo, list-form: sys.executable -m <worker>, com os ids como str.
    assert len(_FakePopen.calls) == 1
    args = _FakePopen.calls[0]
    assert args == [
        sys.executable,
        "-m",
        TRAINING_WORKER,
        "--assignment",
        str(aid),
        "--job-id",
        str(job_id),
    ]
    # Nenhum shell=True / string interpolada: os args são uma lista de str puras.
    assert all(isinstance(a, str) for a in args)


def test_dispatch_rejects_statistics_only_409(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn, status="statistics_only")
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)

    resp = client.post("/training-jobs", json={"assignment_id": aid})
    assert resp.status_code == 409


def test_dispatch_blocked_before_approval_then_ok_after(api_client, monkeypatch):
    # o gate humano — kc_draft (não-aprovado) é 409; aprovar destrava o /training.
    client, conn = api_client
    aid = _seed_assignment(conn, status="kc_draft")
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)

    assert client.post("/training-jobs", json={"assignment_id": aid}).status_code == 409

    SqliteAssignmentRepository(conn).set_status(aid, "kc_approved")
    assert client.post("/training-jobs", json={"assignment_id": aid}).status_code == 202


def test_dispatch_rejects_missing_assignment_409(api_client, monkeypatch):
    client, _ = api_client
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    resp = client.post("/training-jobs", json={"assignment_id": 9999})
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

    resp = client.post("/training-jobs", json={"assignment_id": aid})
    assert resp.status_code == 409


def test_poll_returns_progress_fields(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    job_id = client.post("/training-jobs", json={"assignment_id": aid}).json()["job_id"]

    # Simula o subprocess escrevendo progresso por-época sob WAL (conexão de teste separada).
    SqliteTrainingJobRepository(conn).mark_running(job_id, total_epochs=40, started_at=_NOW)
    # O progresso corrente é DERIVADO da curva append-only, não de um campo mutável.
    SqliteTrainingEpochMetricRepository(conn).append(job_id, TrainingEpochMetric(7, 0.42, _NOW))

    resp = client.get(f"/training-jobs/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["status"] == "running"
    assert body["current_epoch"] == 7
    assert body["total_epochs"] == 40
    assert body["train_loss"] == 0.42


def test_poll_returns_parse_rate(api_client, monkeypatch):
    """O progresso expõe ao professor a taxa de parse gravada pelo worker."""
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    job_id = client.post("/training-jobs", json={"assignment_id": aid}).json()["job_id"]

    # Simula o subprocess concluindo com a taxa de parse gravada (conexão de teste separada).
    SqliteTrainingJobRepository(conn).mark_done(job_id, updated_at=_NOW, java_parse_rate=0.86)

    resp = client.get(f"/training-jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["java_parse_rate"] == 0.86


def test_poll_parse_rate_null_when_unset(api_client, monkeypatch):
    """Um job em andamento, sem taxa de parse gravada, devolve null sem erro."""
    client, conn = api_client
    aid = _seed_assignment(conn)
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    job_id = client.post("/training-jobs", json={"assignment_id": aid}).json()["job_id"]

    resp = client.get(f"/training-jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["java_parse_rate"] is None


def test_poll_missing_job_404(api_client):
    client, _ = api_client
    resp = client.get("/training-jobs/9999")
    assert resp.status_code == 404


def test_loss_history_lists_every_epoch_in_order(api_client, monkeypatch):
    client, conn = api_client
    aid = _seed_assignment(conn)
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    job_id = client.post("/training-jobs", json={"assignment_id": aid}).json()["job_id"]
    metrics = SqliteTrainingEpochMetricRepository(conn)
    metrics.append(job_id, TrainingEpochMetric(2, 0.5, "t2"))
    metrics.append(job_id, TrainingEpochMetric(1, 0.9, "t1"))

    response = client.get(f"/training-jobs/{job_id}/loss-history")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": job_id,
        "epochs": [
            {"epoch": 1, "train_loss": 0.9, "recorded_at": "t1"},
            {"epoch": 2, "train_loss": 0.5, "recorded_at": "t2"},
        ],
    }
    assert client.get("/training-jobs/9999/loss-history").status_code == 404
