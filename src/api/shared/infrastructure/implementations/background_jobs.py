# Jobs pesados rodam em subprocess; o banco é o canal entre processos, o retorno se perde.
from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Callable, Protocol

from api.shared.infrastructure import settings
from api.shared.infrastructure.database.sqlite_connection import connect
from api.shared.infrastructure.implementations.one_job_at_a_time_lock import OneJobAtATimeLock


class SubprocessJobLauncher:
    # IBackgroundJobLauncher via `python -m <worker_module> --assignment N --job-id J`.
    def __init__(self, worker_module: str) -> None:
        self._worker_module = worker_module

    def launch(self, assignment_id: int, job_id: int) -> None:
        launch_worker(self._worker_module, assignment_id, job_id)


# List-form, sem shell=True, ids validados pelo DTO, nunca interpolados numa string.
def launch_worker(module: str, assignment_id: int, job_id: int) -> None:
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            module,
            "--assignment",
            str(int(assignment_id)),
            "--job-id",
            str(int(job_id)),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def worker_main(
    module: str,
    run: Callable[[sqlite3.Connection, int, int], dict | None],
    argv: list[str] | None,
) -> int:
    parser = argparse.ArgumentParser(prog=f"python -m {module}")
    parser.add_argument("--assignment", type=int, required=True, help="assignment.id (SQLite)")
    parser.add_argument("--job-id", type=int, required=True, help="id do job (SQLite)")
    args = parser.parse_args(argv)

    # Caminhos absolutos a partir do env, não do cwd herdado, web e subprocess veem o mesmo dado.
    settings.DB_PATH = os.environ.get("EDMKT_DB_PATH", str(Path(settings.DB_PATH).resolve()))
    settings.DATA_ROOT = Path(os.environ.get("EDMKT_DATA_ROOT", str(settings.DATA_ROOT.resolve())))

    conn = connect(settings.DB_PATH)  # o subprocess abre a SUA própria conexão
    result = run(conn, args.assignment, args.job_id)
    return 0 if result is not None else 1


class _IFailableJobRepository(Protocol):
    def mark_failed(self, job_id: int, error_message: str) -> None: ...


# Adquire a trava como 1º ato e roda `body`; em falha marca o job e libera a trava ao sair.
def run_under_lock(
    conn: sqlite3.Connection,
    operation: str,
    job_id: int,
    job_repo: _IFailableJobRepository,
    body: Callable[[], dict],
    describe_failure: Callable[[Exception], str] = str,
) -> dict | None:
    lock = OneJobAtATimeLock(conn).acquire(operation, job_id=job_id)
    if not lock:
        job_repo.mark_failed(job_id, "pipeline busy")
        return None
    with lock:  # release garantido ao sair, inclusive sob exceção
        try:
            return body()
        except Exception as e:
            job_repo.mark_failed(job_id, describe_failure(e))
            return None
