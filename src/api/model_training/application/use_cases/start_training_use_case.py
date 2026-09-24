# Dispara o treino do Code-DKT em background e devolve o job na hora (o treino leva minutos).

from __future__ import annotations

from api.assignments.domain.entities.assignment_entity import AssignmentStatus
from api.assignments.domain.rules.assignment_in_status_rule import AssignmentInStatusRule
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.model_training.application.dtos.start_training_dto import (
    StartedTrainingJobDTO,
    StartTrainingDTO,
)
from api.model_training.domain.entities.training_job_entity import TrainingJob
from api.model_training.domain.interfaces.training_job_repository import ITrainingJobRepository
from api.shared.application.interfaces.background_job_launcher import IBackgroundJobLauncher
from api.shared.application.services.clock import utc_now_iso
from api.shared.application.interfaces.job_lock import IJobLock
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.interfaces.business_rule import IBusinessRule
from api.shared.domain.errors.another_job_running import AnotherJobRunning
from api.shared.domain.value_objects.job_status import JobStatus


class StartTrainingUseCase(WriteUseCase):
    def __init__(
        self,
        assignments: IAssignmentRepository,
        jobs: ITrainingJobRepository,
        job_lock: IJobLock,
        launcher: IBackgroundJobLauncher,
    ) -> None:
        self._assignments = assignments
        self._jobs = jobs
        self._job_lock = job_lock
        self._launcher = launcher

    def rules(self) -> list[IBusinessRule]:
        # Nada de treino antes de o professor aprovar a Q-matrix.
        return [
            AssignmentInStatusRule(
                self._assignments,
                allowed=(AssignmentStatus.KC_APPROVED,),
                message="Q-matrix ainda não aprovada pelo professor",
            )
        ]

    def _run(self, dto: StartTrainingDTO) -> StartedTrainingJobDTO:
        # Fora das regras de propósito, é corrida, não defeito do pedido (daí AnotherJobRunning).
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
