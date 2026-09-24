"""Dispara o treino do Code-DKT em background e devolve o job na hora (o treino leva minutos)."""

from __future__ import annotations

from api.assignments.domain.assignment_entity import AssignmentStatus
from api.assignments.domain.assignment_in_status_rule import AssignmentInStatusRule
from api.assignments.domain.assignment_repository import AssignmentRepository
from api.model_training.application.start_training_dto import (
    StartedTrainingJobDTO,
    StartTrainingDTO,
)
from api.model_training.domain.training_job_entity import TrainingJob
from api.model_training.domain.training_job_repository import TrainingJobRepository
from api.shared.application.background_job_launcher import BackgroundJobLauncher
from api.shared.application.clock import utc_now_iso
from api.shared.application.job_lock import JobLock
from api.shared.application.write_use_case import WriteUseCase
from api.shared.domain.business_rule import BusinessRule
from api.shared.domain.errors import AnotherJobRunning
from api.shared.domain.job_status import JobStatus


class StartTrainingUseCase(WriteUseCase):
    def __init__(
        self,
        assignments: AssignmentRepository,
        jobs: TrainingJobRepository,
        job_lock: JobLock,
        launcher: BackgroundJobLauncher,
    ) -> None:
        self._assignments = assignments
        self._jobs = jobs
        self._job_lock = job_lock
        self._launcher = launcher

    def rules(self) -> list[BusinessRule]:
        # Nada de treino antes de o professor aprovar a Q-matrix.
        return [
            AssignmentInStatusRule(
                self._assignments,
                allowed=(AssignmentStatus.KC_APPROVED,),
                message="Q-matrix ainda não aprovada pelo professor",
            )
        ]

    def _run(self, dto: StartTrainingDTO) -> StartedTrainingJobDTO:
        # Fora das regras de propósito: é corrida, não defeito do pedido (ver AnotherJobRunning).
        if self._job_lock.is_another_job_running():
            raise AnotherJobRunning("já existe um job em andamento; aguarde a conclusão")
        job_id = self._jobs.add(
            TrainingJob(
                id=None,
                assignment_id=dto.assignment_id,
                status=JobStatus.PENDING,
                created_at=utc_now_iso(),
            )
        )
        self._launcher.launch(dto.assignment_id, job_id)
        return StartedTrainingJobDTO(job_id=job_id, status=JobStatus.PENDING)
