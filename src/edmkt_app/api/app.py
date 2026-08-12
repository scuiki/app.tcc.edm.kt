"""App factory FastAPI — raiz de composição da camada HTTP (D-12).

`create_app()` monta um app com lifespan que, no startup, conecta o app.db, roda as migrations
e RECUPERA qualquer trava órfã. O reclaim é obrigatório: o subprocess de treino registra o
holder_pid na linha pipeline_lock; se o web reinicia com um treino morto no meio, a trava
ficaria presa por um PID que já não existe — reclaim_orphan_lock a libera por liveness de PID,
sem TTL (Fase 2 D-08).

Rode com `--workers 1` (CLAUDE.md: escritor único + GPU compartilhada) e bind NÃO-público
(`127.0.0.1` ou o tailnet `100.96.0.53`, NUNCA `0.0.0.0` — nitro-env). No Docker, publique a
porta com bind IP explícito: `docker run -p 127.0.0.1:PORT:PORT ...` ou
`-p 100.96.0.53:PORT:PORT` — porta bare vaza na LAN bypassando o firewalld.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from edmkt_app.api import dashboard, ingestion, kc, training
from edmkt_app.persistence import connect, run_migrations
from edmkt_app.persistence.lock import reclaim_orphan_lock
from edmkt_app.use_cases.base import NotFound, PipelineBusy, ValidationFailed
from edmkt_app.use_cases.kc_rules import EmptyProblemError


def _resolve_db_path() -> str:
    # Path absoluto a partir do env, não do cwd herdado (Open Q2): o web e o subprocess de
    # treino precisam abrir o MESMO app.db.
    return os.environ.get("EDMKT_DB_PATH", str(Path("app.db").resolve()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = _resolve_db_path()
    conn = connect(db_path)
    try:
        run_migrations(conn)
        reclaim_orphan_lock(conn)
    finally:
        conn.close()
    app.state.db_path = db_path
    yield


def _install_error_handlers(app: FastAPI) -> None:
    """Traduz as recusas da app layer para HTTP num lugar só.

    Sem isto cada rota repetiria o mesmo try/except, e a tradução voltaria a ser copiada. As
    categorias vêm de use_cases.base e não conhecem HTTP; o mapeamento para status code é desta
    camada. O corpo é `{"detail": ...}` — a mesma forma que HTTPException produzia, porque o
    texto e o formato do erro são contrato.
    """

    @app.exception_handler(NotFound)
    def _not_found(_request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValidationFailed)
    def _validation_failed(_request: Request, exc: ValidationFailed) -> JSONResponse:
        # join: com uma mensagem o texto é idêntico ao de antes; o acúmulo só aparece quando um
        # use case tem de fato várias specs recusando o mesmo payload.
        return JSONResponse(status_code=409, content={"detail": "; ".join(exc.messages)})

    @app.exception_handler(PipelineBusy)
    def _pipeline_busy(_request: Request, exc: PipelineBusy) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(EmptyProblemError)
    def _empty_problem(_request: Request, exc: EmptyProblemError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, title="EDM·KT")
    _install_error_handlers(app)
    app.include_router(training.router)
    app.include_router(ingestion.router)
    app.include_router(kc.router)
    app.include_router(dashboard.router)
    return app
