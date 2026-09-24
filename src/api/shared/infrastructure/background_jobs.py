"""Os jobs pesados (treino e geração de KCs) rodam em subprocess, um por vez.

As três metades aqui eram escritas duas vezes, uma por job:

- `launch_worker`: o web dispara o subprocess e volta sem esperar;
- `worker_main`: o `main()` do subprocess resolve os caminhos a partir do env e abre a sua conexão;
- `run_under_lock`: o worker adquire a trava como primeiro ato e, em qualquer falha, marca o job.

O banco é o canal entre os processos: o retorno do subprocess se perde, e o estado vive na linha
do job.
"""

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
from api.shared.infrastructure.one_job_at_a_time_lock import OneJobAtATimeLock


def launch_worker(module: str, assignment_id: int, job_id: int) -> None:
    """Dispara `python -m <module> --assignment N --job-id J` e retorna sem esperar."""
    # List-form, SEM shell=True, ids inteiros validados pelo DTO — nunca interpolados numa string
    # (T-04-CMD). O filho não herda os fds do web: a coordenação é só por SQLite/WAL (IN-03).
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
    """O `main()` de um worker: lê os argumentos, resolve os caminhos e roda o job."""
    parser = argparse.ArgumentParser(prog=f"python -m {module}")
    parser.add_argument("--assignment", type=int, required=True, help="assignment.id (SQLite)")
    parser.add_argument("--job-id", type=int, required=True, help="id do job (SQLite)")
    args = parser.parse_args(argv)

    # Caminhos absolutos a partir do env, não do cwd herdado (Pitfall 2): o web e o subprocess
    # precisam ver o MESMO app.db e o MESMO data/.
    settings.DB_PATH = os.environ.get("EDMKT_DB_PATH", str(Path(settings.DB_PATH).resolve()))
    settings.DATA_ROOT = Path(os.environ.get("EDMKT_DATA_ROOT", str(settings.DATA_ROOT.resolve())))

    conn = connect(settings.DB_PATH)  # o subprocess abre a SUA conexão (Pitfall 2)
    result = run(conn, args.assignment, args.job_id)
    return 0 if result is not None else 1


class _FailableJobRepository(Protocol):
    def mark_failed(self, job_id: int, error_message: str) -> None: ...


def run_under_lock(
    conn: sqlite3.Connection,
    operation: str,
    job_id: int,
    job_repo: _FailableJobRepository,
    body: Callable[[], dict],
    describe_failure: Callable[[Exception], str] = str,
) -> dict | None:
    """Adquire a trava (1º ato) e roda `body`; em falha marca o job e libera a trava.

    Devolve o resultado de `body` no sucesso, ou None quando a trava tem dono vivo ou o job
    falhou — o estado de falha vive todo na linha do job (D-03/D-04). O acquire é aqui, no
    subprocess, e não no web: é ele o gate autoritativo, e o `holder_pid` precisa apontar para o
    processo que de fato faz o trabalho, para a liveness de PID recuperar a trava se ele morrer.
    """
    lock = OneJobAtATimeLock(conn).acquire(operation, job_id=job_id)
    if not lock:
        job_repo.mark_failed(job_id, "pipeline busy")
        return None
    with lock:  # release garantido ao sair E sob exceção (SC3)
        try:
            return body()
        except Exception as e:
            job_repo.mark_failed(job_id, describe_failure(e))
            return None
