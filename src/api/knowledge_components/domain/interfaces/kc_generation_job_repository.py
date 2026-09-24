# Interface de persistência dos jobs de geração de KCs, a ponte entre o web e o subprocess.
from __future__ import annotations

from typing import Protocol

from api.knowledge_components.domain.entities.kc_generation_job_entity import (
    KnowledgeComponentGenerationJob,
)


class IKnowledgeComponentGenerationJobRepository(Protocol):
    def add(self, job: KnowledgeComponentGenerationJob) -> int: ...

    def get(self, job_id: int) -> KnowledgeComponentGenerationJob | None: ...

    def mark_running(self, job_id: int, started_at: str) -> None: ...

    def update_stage(self, job_id: int, stage: str, updated_at: str) -> None: ...

    def mark_done(self, job_id: int, updated_at: str) -> None: ...

    def mark_failed(self, job_id: int, error_message: str) -> None: ...
