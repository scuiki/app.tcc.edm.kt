# O app FastAPI, a raiz que monta os controllers de cada funcionalidade.
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from api.assignments.presentation.controllers import assignments_controller
from api.classrooms.presentation.controllers import classrooms_controller
from api.assignments.problems.presentation.controllers import problems_controller
from api.classroom_import.presentation.controllers import classroom_import_controller
from api.knowledge_components.presentation.controllers import knowledge_components_controller
from api.mastery_dashboard.presentation.controllers import mastery_dashboard_controller
from api.model_training.presentation.controllers import training_controller
from api.shared.infrastructure.database.migrations.runner import run_migrations
from api.shared.infrastructure.database.sqlite_connection import connect
from api.shared.infrastructure.implementations.one_job_at_a_time_lock import (
    release_lock_of_dead_holder,
)
from api.shared.presentation.http.error_handlers import install_error_handlers


# Caminho absoluto do env, não do cwd herdado, web e subprocessos precisam abrir o MESMO app.db.
def _resolve_db_path() -> str:
    return os.environ.get("EDMKT_DB_PATH", str(Path("app.db").resolve()))


# Libera no startup uma trava cujo dono morreu, um job que morreu no meio a deixaria presa.
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


# Rode com --workers 1, escritor único do SQLite e GPU compartilhada exigem processo único.
def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, title="EDM·KT")
    install_error_handlers(app)
    # Na ordem do fluxo do professor, importar, gerar e aprovar KCs, treinar, acompanhar.
    app.include_router(classrooms_controller.router)
    app.include_router(assignments_controller.router)
    app.include_router(problems_controller.router)
    app.include_router(classroom_import_controller.router)
    app.include_router(knowledge_components_controller.router)
    app.include_router(training_controller.router)
    app.include_router(mastery_dashboard_controller.router)
    return app
