"""KnowledgeComponentGenerationJob: uma geração de KCs em andamento ou concluída."""

from __future__ import annotations

from dataclasses import dataclass

from api.shared.domain.job_status import JobStatus


@dataclass
class KnowledgeComponentGenerationJob:
    id: int | None
    assignment_id: int
    status: JobStatus
    created_at: str
    # A etapa do KCGen-KT em que o job está (generate, cluster, qmatrix): o progresso aqui tem
    # etapas nomeadas, não épocas.
    stage: str | None = None
    started_at: str | None = None
    updated_at: str | None = None
    error_message: str | None = None
