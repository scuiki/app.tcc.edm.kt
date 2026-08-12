"""Trava + tratamento de falha, separado do CLI para ser chamável direto no teste."""

from __future__ import annotations

import torch

from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.lock import PipelineLock
from edmkt_app.train.stages import _train_body


def _run_training(conn, assignment_id: int, job_id: int) -> dict | None:
    """Adquire a trava (1º ato, D-02) e roda o treino; em falha marca o job e libera a trava.

    Retorna o dict de resultado (parse_rate/artifact_id/first_auc) no sucesso, ou None quando
    a trava está ocupada ou o treino falhou — o estado de falha vive todo no TrainingJob (D-03).
    """
    job_repo = repos.TrainingJobRepository(conn)
    lock = PipelineLock(conn).acquire("training", job_id=job_id)
    if not lock:
        job_repo.mark_failed(job_id, "pipeline busy")
        return None
    with lock:  # release garantido ao sair E sob exceção (SC3)
        try:
            return _train_body(conn, assignment_id, job_id)
        except torch.cuda.OutOfMemoryError:
            # D-11/Pitfall 4: VRAM da RTX 4050 (6 GB) estourou — falha com graça, sem detalhe
            # de tensor. O assignment segue trainable (nunca foi flipado).
            job_repo.mark_failed(
                job_id, "VRAM insuficiente para o treino; tente menos dados ou CPU"
            )
            return None
        except Exception as e:
            job_repo.mark_failed(job_id, str(e))
            return None
