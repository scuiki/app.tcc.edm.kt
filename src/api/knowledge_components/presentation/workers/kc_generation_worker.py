# Subprocess da geração de KCs, pega a trava de job como primeiro ato e roda o use case.
from __future__ import annotations

import sqlite3
import sys

from api.knowledge_components.infrastructure.repositories.sqlite_kc_generation_job_repository import (
    SqliteKnowledgeComponentGenerationJobRepository,
)
from api.knowledge_components.presentation.dependencies import (
    KC_GENERATION_WORKER,
    build_run_kc_generation_use_case,
)
from api.shared.infrastructure.implementations.background_jobs import run_under_lock, worker_main


def run_kc_generation(conn: sqlite3.Connection, assignment_id: int, job_id: int, llm=None) -> dict | None:
    # Roda a geração sob a trava, devolve o resumo no sucesso ou None na falha.
    use_case = build_run_kc_generation_use_case(conn, llm=llm)
    return run_under_lock(
        conn,
        "kc_generation",
        job_id,
        SqliteKnowledgeComponentGenerationJobRepository(conn),
        lambda: use_case.execute(assignment_id, job_id),
    )


def main(argv: list[str] | None = None) -> int:
    return worker_main(KC_GENERATION_WORKER, run_kc_generation, argv)


if __name__ == "__main__":
    sys.exit(main())
