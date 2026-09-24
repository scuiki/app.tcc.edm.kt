"""O subprocess do treino: `python -m api.model_training.presentation.training_worker`.

Pega a trava de job como PRIMEIRO ato, para que a liveness de PID recupere a trava se o treino
morrer: o dono da trava precisa ser o processo que de fato treina, não o web.
"""

from __future__ import annotations

import sqlite3
import sys

import torch

from api.model_training.infrastructure.sqlite_training_job_repository import (
    SqliteTrainingJobRepository,
)
from api.model_training.presentation.dependencies import (
    TRAINING_WORKER,
    build_run_training_use_case,
)
from api.shared.infrastructure.implementations.background_jobs import run_under_lock, worker_main


def describe_training_failure(error: Exception) -> str:
    # A VRAM da RTX 4050 (6 GB) estourou: uma mensagem que o professor entende, sem detalhe de
    # tensor. O assignment segue kc_approved (nunca foi publicado).
    if isinstance(error, torch.cuda.OutOfMemoryError):
        return "VRAM insuficiente para o treino; tente menos dados ou CPU"
    return str(error)


def run_training(conn: sqlite3.Connection, assignment_id: int, job_id: int, trainer=None) -> dict | None:
    """Roda o treino sob a trava. Devolve o resumo no sucesso, ou None na falha."""
    use_case = build_run_training_use_case(conn, trainer=trainer)
    return run_under_lock(
        conn,
        "training",
        job_id,
        SqliteTrainingJobRepository(conn),
        lambda: use_case.execute(assignment_id, job_id),
        describe_failure=describe_training_failure,
    )


def main(argv: list[str] | None = None) -> int:
    return worker_main(TRAINING_WORKER, run_training, argv)


if __name__ == "__main__":
    sys.exit(main())
