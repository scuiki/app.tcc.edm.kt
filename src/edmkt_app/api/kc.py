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
from edmkt_app.persistence import models, transaction
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.lock import pid_alive

router = APIRouter(tags=["kc"])


class KCGenerateRequest(BaseModel):
    assignment_id: int  # ASVS V5: int, nunca string — fecha command injection na borda (T-05-CMD)


class KCRenameRequest(BaseModel):
    name: str  # dado do professor (KC-02): SQL parametrizado, nunca interpolado (T-05-11)


class KCAddRequest(BaseModel):
    assignment_id: int
    name: str
    problem_ids: list[int] = []  # bindings opcionais; ints validados pelo Pydantic


class KCMergeRequest(BaseModel):
    assignment_id: int
    kc_keep: int
    kc_drop: int


class KCApproveRequest(BaseModel):
    assignment_id: int


class _EmptyProblemError(Exception):
    """A invariante 0-KC seria violada (D-07): levantada DENTRO da txn → ROLLBACK."""


def _assert_no_empty_problem(
    conn: sqlite3.Connection, assignment_id: int, problems: list[int]
) -> None:
    # D-07 (guarda dura): qualquer problema afetado pela edição que ficou com 0 KCs aborta a
    # operação inteira. Roda DENTRO do `with transaction` → o raise vira ROLLBACK.
    qrepo = repos.QMatrixRepository(conn)
    for problem_id in problems:
        if qrepo.kc_count_for_problem(assignment_id, problem_id) == 0:
            raise _EmptyProblemError(
                f"problema {problem_id} ficaria com 0 KCs — edição bloqueada (D-07)"
            )


def _revert_approval_if_approved(conn: sqlite3.Connection, assignment_id: int) -> None:
    # D-06: editar a Q-matrix após aprovar reverte kc_approved → kc_draft (re-aprovação exigida).
    arepo = repos.AssignmentRepository(conn)
    assignment = arepo.get(assignment_id)
    if assignment is not None and assignment.status == "kc_approved":
        arepo.set_status(assignment_id, "kc_draft")


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


# --- edição síncrona da Q-matrix (KC-02, D-07) + aprovação (KC-03, D-06) ----------
# Sem subprocess: são writes diretos no SQLite. CADA mutação roda numa única
# `with transaction(conn)`; a guarda 0-KC levanta DENTRO da txn → ROLLBACK (D-07), e a edição
# reverte uma aprovação prévia (D-06). ids inteiros pelo Pydantic; nomes são dado, nunca shell/SQL.


@router.patch("/kc/{kc_id}")
def rename_kc(
    kc_id: int,
    body: KCRenameRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    kc_repo = repos.KCRepository(conn)
    kc = kc_repo.get(kc_id)
    if kc is None:
        raise HTTPException(status_code=404, detail="KC inexistente")
    # rename não mexe na qmatrix → nenhum problema pode zerar; só a reversão de aprovação aplica.
    with transaction(conn):
        kc_repo.rename(kc_id, body.name)
        _revert_approval_if_approved(conn, kc.assignment_id)
    return {"id": kc_id, "name": body.name}


@router.post("/kc", status_code=201)
def add_kc(
    body: KCAddRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    kc_repo = repos.KCRepository(conn)
    qmatrix_repo = repos.QMatrixRepository(conn)
    with transaction(conn):
        # KC do professor nasce com kc_index NULL (não veio de um cluster TCC — 05-01).
        kc_id = kc_repo.insert(
            models.KC(id=None, assignment_id=body.assignment_id, name=body.name, kc_index=None)
        )
        qmatrix_repo.insert_bindings(body.assignment_id, kc_id, body.problem_ids)
        # adicionar só PODE aumentar a cobertura → a guarda 0-KC não pode falhar aqui, mas a
        # edição ainda reverte uma aprovação (D-06).
        _revert_approval_if_approved(conn, body.assignment_id)
    return {"id": kc_id, "name": body.name}


@router.delete("/kc/{kc_id}")
def remove_kc(
    kc_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    kc_repo = repos.KCRepository(conn)
    qmatrix_repo = repos.QMatrixRepository(conn)
    kc = kc_repo.get(kc_id)
    if kc is None:
        raise HTTPException(status_code=404, detail="KC inexistente")
    assignment_id = kc.assignment_id
    # Colhe os problemas que este KC liga ANTES de remover — são os únicos que podem zerar (D-07).
    affected = qmatrix_repo.problems_of_kc(kc_id)
    try:
        with transaction(conn):
            qmatrix_repo.delete_by_kc(kc_id)
            kc_repo.delete(kc_id)
            _assert_no_empty_problem(conn, assignment_id, affected)  # raise → ROLLBACK
            _revert_approval_if_approved(conn, assignment_id)
    except _EmptyProblemError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"deleted": kc_id}


@router.post("/kc/merge")
def merge_kc(
    body: KCMergeRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    kc_repo = repos.KCRepository(conn)
    qmatrix_repo = repos.QMatrixRepository(conn)
    if kc_repo.get(body.kc_keep) is None or kc_repo.get(body.kc_drop) is None:
        raise HTTPException(status_code=404, detail="KC inexistente")
    # merge = união de bindings (kc_drop → kc_keep); os problemas de kc_drop é que poderiam zerar.
    affected = qmatrix_repo.problems_of_kc(body.kc_drop)
    try:
        with transaction(conn):
            qmatrix_repo.repoint_bindings(body.assignment_id, body.kc_keep, body.kc_drop)
            kc_repo.delete(body.kc_drop)
            _assert_no_empty_problem(conn, body.assignment_id, affected)  # raise → ROLLBACK
            _revert_approval_if_approved(conn, body.assignment_id)
    except _EmptyProblemError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"kc_keep": body.kc_keep, "kc_drop": body.kc_drop}
