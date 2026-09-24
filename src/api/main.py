"""O app FastAPI: a raiz que monta os controllers de cada funcionalidade.

No startup o lifespan conecta ao app.db, aplica as migrations e libera uma trava cujo dono morreu:
um job que morreu no meio deixaria a OneJobAtATimeLock presa por um PID que já não existe.

Rode com `--workers 1` (escritor único do SQLite + GPU compartilhada) e sem publicar porta sem bind
IP explícito (nitro-env): no compose, só o frontend publica porta.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from api.shared.infrastructure.database.migrations.runner import run_migrations
from api.shared.infrastructure.database.sqlite_connection import connect
from api.shared.infrastructure.one_job_at_a_time_lock import release_lock_of_dead_holder
from api.shared.presentation.http.error_handlers import install_error_handlers
from api.assignments.presentation import assignments_controller
from edmkt_app.api import dashboard, ingestion, kc, training


def _resolve_db_path() -> str:
    # Caminho absoluto do env, não do cwd herdado: o web e os subprocessos de job precisam abrir o
    # MESMO app.db.
    return os.environ.get("EDMKT_DB_PATH", str(Path("app.db").resolve()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = _resolve_db_path()
    conn = connect(db_path)
    try:
        run_migrations(conn)
        release_lock_of_dead_holder(conn)
    finally:
        conn.close()
    app.state.db_path = db_path
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, title="EDM·KT")
    install_error_handlers(app)
    app.include_router(assignments_controller.router)
    app.include_router(training.router)
    app.include_router(ingestion.router)
    app.include_router(kc.router)
    app.include_router(dashboard.router)
    return app
