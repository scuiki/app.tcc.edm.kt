"""Router /training — HTTP puro: recebe, delega ao use case, devolve.

Nenhuma regra de negócio mora aqui. O gate de Q-matrix aprovada é uma specification
(specs.AssignmentInStatus), o pré-check de pipeline ocupado é do use case, e a tradução das
recusas para status code está nos handlers de api/app.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from edmkt_app.api.deps import get_training_status_uc, start_training_uc
from edmkt_app.use_cases.get_training_status import GetTrainingStatusUseCase
from edmkt_app.use_cases.start_training import StartTrainingDto, StartTrainingUseCase

router = APIRouter(tags=["training"])


@router.post("/training", status_code=202)
def dispatch_training(
    body: StartTrainingDto,
    uc: StartTrainingUseCase = Depends(start_training_uc),
) -> dict:
    return uc.execute(body)


@router.get("/training/{job_id}")
def poll_training(
    job_id: int,
    uc: GetTrainingStatusUseCase = Depends(get_training_status_uc),
) -> dict:
    return uc.execute(job_id)
