"""Dispara o treino Code-DKT em subprocess (MODEL-01/02, D-02)."""

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


class StartTrainingDto(BaseModel):
    assignment_id: int  # ASVS V5: int, nunca string — fecha command injection na borda (T-04-INPUT)


class StartTrainingUseCase(BaseWriteUseCase):
    specs = [
        # KC-03: sem treino antes da aprovação da Q-matrix pelo professor. O fluxo de estado é
        # trainable → kc_draft → kc_approved → trained.
        specs.AssignmentInStatus(
            allowed=("kc_approved",), message="Q-matrix ainda não aprovada pelo professor"
        )
    ]

    def _run(self, dto: StartTrainingDto) -> dict:
        # Fora do registry de propósito: corrida, não regra do payload (ver PipelineBusy).
        if pipeline_busy(self._conn):
            raise PipelineBusy("pipeline ocupado; aguarde o treino atual")

        job_id = repos.TrainingJobRepository(self._conn).insert(
            models.TrainingJob(
                id=None,
                assignment_id=dto.assignment_id,
                status="pending",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        # Dispatch list-form, SEM shell=True, ids inteiros validados pelo DTO — nunca
        # interpolados numa string (T-04-CMD). Retorna sem esperar: o treino roda fora do web.
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "edmkt_app.train",
                "--assignment",
                str(dto.assignment_id),
                "--job-id",
                str(job_id),
            ],
            # IN-03: o filho não herda os fds do web — coordenação é só por SQLite/WAL.
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"job_id": job_id, "status": "pending"}
