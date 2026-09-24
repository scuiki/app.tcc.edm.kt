"""Traduz as recusas do domínio para HTTP num lugar só.

Sem isto cada rota repetiria o mesmo try/except. O corpo é `{"detail": ...}`, a mesma forma que
HTTPException produz, porque o texto e o formato do erro fazem parte do contrato.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.shared.domain.errors import AnotherJobRunning, BusinessRuleViolation, NotFound


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    def _not_found(_request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(BusinessRuleViolation)
    def _rule_violated(_request: Request, exc: BusinessRuleViolation) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "; ".join(exc.messages)})

    @app.exception_handler(AnotherJobRunning)
    def _another_job_running(_request: Request, exc: AnotherJobRunning) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})
