# KnowledgeComponentGenerationJob, uma geração de KCs em andamento ou concluída.
from __future__ import annotations

from dataclasses import dataclass

from api.shared.domain.value_objects.job_status import JobStatus


@dataclass
class KnowledgeComponentGenerationJob:
    id: int | None
    assignment_id: int
    status: JobStatus
    created_at: str
    # Etapa do KCGen-KT (generate, cluster, qmatrix), progresso nomeado, não são épocas.
    stage: str | None = None
    started_at: str | None = None
    updated_at: str | None = None
    error_message: str | None = None
