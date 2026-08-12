"""Dispara o pipeline KCGen-KT em subprocess (KC-01, D-05)."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone

from pydantic import BaseModel

from edmkt_app import specs
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.lock import pipeline_busy
from edmkt_app.use_cases.base import BaseWriteUseCase, PipelineBusy


class GenerateKCsDto(BaseModel):
    assignment_id: int  # ASVS V5: int, nunca string — fecha command injection na borda (T-05-CMD)


class GenerateKCsUseCase(BaseWriteUseCase):
    specs = [
        # KC-gen roda sobre um assignment treinável e ainda-não-rascunhado (gate da Fase 3).
        specs.AssignmentInStatus(
            allowed=("trainable",), message="assignment não está trainable"
        )
    ]

    def _run(self, dto: GenerateKCsDto) -> dict:
        if pipeline_busy(self._conn):
            raise PipelineBusy("pipeline ocupado; aguarde o job atual")

        job_id = repos.KCJobRepository(self._conn).insert(
            models.KCJob(
                id=None,
                assignment_id=dto.assignment_id,
                status="pending",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "edmkt_app.kc_pipeline",
                "--assignment",
                str(dto.assignment_id),
                "--job-id",
                str(job_id),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"job_id": job_id, "status": "pending"}
