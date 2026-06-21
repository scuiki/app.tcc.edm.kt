"""Router /kc — POST dispara o subprocess de KC-gen, GET faz poll do estágio (KC-01, D-05).

Espelha api/training.py: o handler NÃO gera KCs — valida o assignment, faz um pré-check barato
da trava, insere um KCJob pendente e dispara `python -m edmkt_app.kc_pipeline` como processo OS
separado, devolvendo o job_id 202 NA HORA. O GET lê a linha do KCJob sob WAL enquanto o
subprocess escreve o estágio (sample/generate/cluster/label/qmatrix).

Escopo deste módulo: generate + poll. As rotas síncronas de edição/merge/approve da Q-matrix
(KC-02/KC-03) vivem no plano seguinte; o `router` é estendido lá.
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

router = APIRouter(tags=["kc"])


class KCGenerateRequest(BaseModel):
    assignment_id: int  # ASVS V5: int, nunca string — fecha command injection na borda (T-05-CMD)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pipeline_busy(conn: sqlite3.Connection) -> bool:
    # Pré-check BARATO e NÃO-autoritativo (D-05): lê o holder sem adquirir. O acquire autoritativo
    # é do subprocess (1º ato); se dois POSTs correrem, o segundo perde o acquire LÁ e marca seu
    # próprio job failed 'busy' — aqui só rejeitamos o "ocupado óbvio" cedo.
    row = conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()
    return row is not None and row["holder_pid"] is not None and pid_alive(row["holder_pid"])


@router.post("/kc/generate", status_code=202)
def dispatch_kc_generate(
    body: KCGenerateRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    assignment = repos.AssignmentRepository(conn).get(body.assignment_id)
    if assignment is None or assignment.status != "trainable":
        # KC-gen roda sobre um assignment treinável e ainda-não-rascunhado (gate da Fase 3).
        raise HTTPException(status_code=409, detail="assignment não está trainable")
    if _pipeline_busy(conn):
        raise HTTPException(status_code=409, detail="pipeline ocupado; aguarde o job atual")

    job_id = repos.KCJobRepository(conn).insert(
        models.KCJob(
            id=None, assignment_id=body.assignment_id, status="pending", created_at=_now_iso()
        )
    )
    # Dispatch list-form, sem invocar shell, ids inteiros validados pelo Pydantic — nunca
    # interpolados numa string (T-05-CMD). Retorna sem esperar: o KC-gen roda fora do web.
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "edmkt_app.kc_pipeline",
            "--assignment",
            str(body.assignment_id),
            "--job-id",
            str(job_id),
        ]
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/kc/jobs/{job_id}")
def poll_kc_job(
    job_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    # Leitura WAL concorrente ao subprocess que escreve o estágio (D-05): conexão própria
    # (Pitfall 2), busy_timeout cobre a rara janela de checkpoint.
    job = repos.KCJobRepository(conn).get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job inexistente")
    return {
        "job_id": job.id,
        "status": job.status,
        "stage": job.stage,  # estágio nomeado do KCGen-KT em vez de época numérica (D-05)
        "error_message": job.error_message,
    }
