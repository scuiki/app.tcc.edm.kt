"""Trava + orquestração do KC-gen, separada do CLI para ser chamável direto no teste."""

from __future__ import annotations

from edmkt_app.background_jobs import run_under_lock
from edmkt_app.kc_pipeline.stages import _kc_body
from edmkt_app.persistence import repositories as repos


def _run_kc_pipeline(conn, assignment_id: int, job_id: int) -> dict | None:
    """Roda o KC-gen sob a trava — nunca concorre com o treino (D-05/MODEL-03).

    Em falha de conteúdo (EmptyContentError/EmptyKCError) ou qualquer outra exceção, o job falha e
    NADA parcial é persistido (D-04): a transação de persistência nem chegou a abrir, ou deu
    ROLLBACK. O assignment segue sem KCs (nunca foi flipado).
    """
    return run_under_lock(
        conn,
        "kc_gen",
        job_id,
        repos.KCJobRepository(conn),
        lambda: _kc_body(conn, assignment_id, job_id),
    )
