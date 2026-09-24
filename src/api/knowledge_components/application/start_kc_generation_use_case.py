"""Dispara a geração de KCs em background e devolve o job na hora (o KCGen-KT leva minutos)."""

from __future__ import annotations

from api.assignments.domain.assignment_entity import AssignmentStatus
from api.assignments.domain.assignment_in_status_rule import AssignmentInStatusRule
from api.assignments.domain.assignment_repository import AssignmentRepository
from api.knowledge_components.application.start_kc_generation_dto import (
    StartedJobDTO,
    StartKnowledgeComponentGenerationDTO,
)
from api.knowledge_components.domain.kc_generation_job_entity import (
    KnowledgeComponentGenerationJob,
)
from api.knowledge_components.domain.kc_generation_job_repository import (
    KnowledgeComponentGenerationJobRepository,
)
from api.shared.application.interfaces.background_job_launcher import IBackgroundJobLauncher
from api.shared.application.services.clock import utc_now_iso
from api.shared.application.interfaces.job_lock import IJobLock
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.interfaces.business_rule import IBusinessRule
from api.shared.domain.errors.another_job_running import AnotherJobRunning
from api.shared.domain.value_objects.job_status import JobStatus


class StartKnowledgeComponentGenerationUseCase(WriteUseCase):
    def __init__(
        self,
        assignments: AssignmentRepository,
        jobs: KnowledgeComponentGenerationJobRepository,
        job_lock: IJobLock,
        launcher: IBackgroundJobLauncher,
    ) -> None:
        self._assignments = assignments
        self._jobs = jobs
        self._job_lock = job_lock
        self._launcher = launcher

    def rules(self) -> list[IBusinessRule]:
        # Gera KCs sobre um assignment com as duas classes e ainda sem rascunho.
        return [
            AssignmentInStatusRule(
                self._assignments,
                allowed=(AssignmentStatus.READY_FOR_KC_GENERATION,),
                message="assignment não está pronto para gerar KCs",
            )
        ]

    def _run(self, dto: StartKnowledgeComponentGenerationDTO) -> StartedJobDTO:
        # Fora das regras de propósito: é corrida, não defeito do pedido (ver AnotherJobRunning).
        if self._job_lock.is_another_job_running():
            raise AnotherJobRunning("já existe um job em andamento; aguarde a conclusão")
        job_id = self._jobs.add(
            KnowledgeComponentGenerationJob(
                id=None,
                assignment_id=dto.assignment_id,
                status=JobStatus.PENDING,
                created_at=utc_now_iso(),
            )
        )
        self._launcher.launch(dto.assignment_id, job_id)
        return StartedJobDTO(job_id=job_id, status=JobStatus.PENDING)
