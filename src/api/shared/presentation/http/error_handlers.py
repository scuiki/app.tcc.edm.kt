# Traduz as recusas do domínio para HTTP num lugar só, o corpo é `{"detail": ...}` do HTTPException.
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.shared.domain.errors.another_job_running import AnotherJobRunning
from api.shared.domain.errors.business_rule_violation import BusinessRuleViolation
from api.shared.domain.errors.not_found import NotFound


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
