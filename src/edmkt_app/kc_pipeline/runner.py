"""Trava + orquestração do KC-gen, separada do CLI para ser chamável direto no teste."""

from __future__ import annotations

from edmkt_app.kc_pipeline.stages import _kc_body
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.lock import PipelineLock


def _run_kc_pipeline(conn, assignment_id: int, job_id: int) -> dict | None:
    """Adquire a trava (1º ato, D-05) e roda o KC-gen; em falha marca o job e libera a trava.

    Retorna o dict de resultado no sucesso, ou None quando a trava está ocupada por um dono vivo
    (segundo perdedor marca seu próprio job 'busy') ou o pipeline falhou — o estado de falha vive
    todo no KCJob (D-04), sem Q-matrix parcial."""
    job_repo = repos.KCJobRepository(conn)
    # Lock é o PRIMEIRO ato — KC-gen nunca concorre com training (D-05/MODEL-03).
    lock = PipelineLock(conn).acquire("kc_gen", job_id=job_id)
    if not lock:
        job_repo.mark_failed(job_id, "pipeline busy")
        return None
    with lock:  # release garantido ao sair E sob exceção (SC3)
        try:
            return _kc_body(conn, assignment_id, job_id)
        except Exception as e:
            # Conteúdo-vazio (EmptyContentError/EmptyKCError) ou qualquer exceção: job falha e
            # NADA parcial é persistido (D-04) — a txn de persistência nem chegou a abrir, ou
            # deu ROLLBACK. O assignment segue 'trainable' (nunca foi flipado).
            job_repo.mark_failed(job_id, str(e))
            return None
