"""Trava + tratamento de falha, separado do CLI para ser chamável direto no teste."""

from __future__ import annotations

import torch

from api.shared.infrastructure.background_jobs import run_under_lock
from edmkt_app.persistence import repositories as repos
from edmkt_app.train.stages import _train_body


def _describe_training_failure(error: Exception) -> str:
    # D-11/Pitfall 4: a VRAM da RTX 4050 (6 GB) estourou — falha com graça, sem detalhe de tensor.
    # O assignment segue kc_approved (nunca foi flipado).
    if isinstance(error, torch.cuda.OutOfMemoryError):
        return "VRAM insuficiente para o treino; tente menos dados ou CPU"
    return str(error)


def _run_training(conn, assignment_id: int, job_id: int) -> dict | None:
    """Roda o treino sob a trava. Devolve parse_rate/artifact_id/first_auc, ou None na falha."""
    return run_under_lock(
        conn,
        "training",
        job_id,
        repos.TrainingJobRepository(conn),
        lambda: _train_body(conn, assignment_id, job_id),
        describe_failure=_describe_training_failure,
    )
