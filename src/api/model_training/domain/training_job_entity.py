"""TrainingJob: um treino do Code-DKT em andamento ou concluído."""

from __future__ import annotations

from dataclasses import dataclass

from api.shared.domain.job_status import JobStatus


@dataclass
class TrainingJob:
    id: int | None
    assignment_id: int
    status: JobStatus
    created_at: str
    # O progresso por época vive em TrainingEpochMetric; aqui só o total, gravado ao começar.
    total_epochs: int | None = None
    started_at: str | None = None
    updated_at: str | None = None
    error_message: str | None = None
    # A fração dos snapshots que o javalang conseguiu parsear, gravada no sucesso: o professor vê
    # quanto do código dos alunos o modelo de fato enxergou.
    java_parse_rate: float | None = None
