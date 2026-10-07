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
    # Etapa do KCGen-KT (generate, cluster, qmatrix, evidence, translate), não são épocas
    stage: str | None = None
    started_at: str | None = None
    updated_at: str | None = None
    error_message: str | None = None
    # Dentro do estágio, quantos itens já terminaram e de quantos, vazio sem itens para contar
    progress_done: int | None = None
    progress_total: int | None = None
    # O modelo de linguagem e a versão do prompt que geraram os KCs, gravados no fim da extração
    model_id: str | None = None
    prompt_version: str | None = None
