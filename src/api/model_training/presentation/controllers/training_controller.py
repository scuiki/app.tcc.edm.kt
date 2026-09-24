"""As rotas de /training-jobs: HTTP puro. Recebe, delega ao use case, devolve."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.model_training.application.dtos.get_training_job_dto import (
    TrainingJobDTO,
    TrainingLossHistoryDTO,
)
from api.model_training.application.use_cases.get_training_job_use_case import GetTrainingJobUseCase
from api.model_training.application.use_cases.get_training_loss_history_use_case import (
    GetTrainingLossHistoryUseCase,
)
from api.model_training.application.dtos.start_training_dto import (
    StartedTrainingJobDTO,
    StartTrainingDTO,
)
from api.model_training.application.use_cases.start_training_use_case import StartTrainingUseCase
from api.model_training.presentation import dependencies

router = APIRouter(prefix="/training-jobs", tags=["model_training"])


@router.post("", status_code=202, response_model=StartedTrainingJobDTO)
def start_training(
    body: StartTrainingDTO,
    use_case: StartTrainingUseCase = Depends(dependencies.start_training_use_case),
) -> StartedTrainingJobDTO:
    return use_case.execute(body)


@router.get("/{job_id}", response_model=TrainingJobDTO)
def get_training_job(
    job_id: int,
    use_case: GetTrainingJobUseCase = Depends(dependencies.get_training_job_use_case),
) -> TrainingJobDTO:
    return use_case.execute(job_id)


@router.get("/{job_id}/loss-history", response_model=TrainingLossHistoryDTO)
def get_training_loss_history(
    job_id: int,
    use_case: GetTrainingLossHistoryUseCase = Depends(
        dependencies.get_training_loss_history_use_case
    ),
) -> TrainingLossHistoryDTO:
    return use_case.execute(job_id)
