"""Router de treino — POST dispara o subprocess, GET faz poll do progresso (MODEL-01/02).

O handler NÃO treina (D-01): valida o assignment, faz um pré-check barato da trava, insere um
TrainingJob pendente e dispara `python -m edmkt_app.train` como processo OS separado, devolvendo
o job_id 202 NA HORA — a requisição não bloqueia enquanto o treino roda. O GET lê a linha do
TrainingJob sob WAL (D-04) enquanto o subprocess escreve o progresso por-época.
"""

from __future__ import annotations

import subprocess
import sqlite3
import sys
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from edmkt_app.api.deps import get_conn
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.lock import pid_alive

router = APIRouter(tags=["training"])


class TrainRequest(BaseModel):
    assignment_id: int  # ASVS V5: int, nunca string — fecha command injection na borda (T-04-INPUT)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pipeline_busy(conn: sqlite3.Connection) -> bool:
    # Pré-check BARATO e NÃO-autoritativo (D-02): lê o holder sem adquirir. O acquire autoritativo
    # é do subprocess; se dois POSTs correrem, o segundo perde o acquire LÁ e marca seu próprio job
    # failed 'busy' (Open Q1) — aqui só rejeitamos o "ocupado óbvio" cedo.
    row = conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()
    return row is not None and row["holder_pid"] is not None and pid_alive(row["holder_pid"])


@router.post("/training", status_code=202)
def dispatch_training(
    body: TrainRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    assignment = repos.AssignmentRepository(conn).get(body.assignment_id)
    if assignment is None or assignment.status != "kc_approved":
        # KC-03: o guard exige kc_approved — sem treino antes da aprovação da Q-matrix pelo
        # professor. O fluxo de estado é trainable → kc_draft → kc_approved → (trained).
        raise HTTPException(status_code=409, detail="Q-matrix ainda não aprovada pelo professor")
    if _pipeline_busy(conn):
        raise HTTPException(status_code=409, detail="pipeline ocupado; aguarde o treino atual")

    job_id = repos.TrainingJobRepository(conn).insert(
        models.TrainingJob(
            id=None, assignment_id=body.assignment_id, status="pending", created_at=_now_iso()
        )
    )
    # Dispatch list-form, SEM shell=True, ids inteiros validados pelo Pydantic — nunca
    # interpolados numa string (T-04-CMD). Retorna sem esperar: o treino roda fora do processo web.
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "edmkt_app.train",
            "--assignment",
            str(body.assignment_id),
            "--job-id",
            str(job_id),
        ],
        # IN-03: o filho não herda os fds do web (socket/pipe) — coordenação é só por SQLite/WAL.
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/training/{job_id}")
def poll_training(
    job_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    # Leitura WAL concorrente ao subprocess que escreve o progresso (D-04): conexão própria
    # (Pitfall 2), busy_timeout cobre a rara janela de checkpoint.
    job = repos.TrainingJobRepository(conn).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job inexistente")
    return {
        "job_id": job.id,
        "status": job.status,
        "current_epoch": job.current_epoch,
        "total_epochs": job.total_epochs,
        "train_loss": job.train_loss,
        "error_message": job.error_message,
        "parse_rate": job.parse_rate,  # cobertura de parse javalang surfaced ao professor (SC-3)
    }
