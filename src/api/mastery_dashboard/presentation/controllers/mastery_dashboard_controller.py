# As rotas de /mastery-dashboard são HTTP puro e só leitura; a única escrita é do use case.

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.mastery_dashboard.application.use_cases.get_mastery_use_case import GetMasteryUseCase
from api.mastery_dashboard.application.use_cases.get_pre_training_statistics_use_case import (
    GetPreTrainingStatisticsUseCase,
)
from api.mastery_dashboard.application.use_cases.get_recommendations_use_case import (
    GetRecommendationsUseCase,
)
from api.mastery_dashboard.application.dtos.mastery_dashboard_dto import (
    MasteryResponseDTO,
    PreTrainingStatisticsResponseDTO,
    RecommendationsResponseDTO,
)
from api.mastery_dashboard.presentation import dependencies

router = APIRouter(prefix="/mastery-dashboard/{assignment_id}", tags=["mastery_dashboard"])


@router.get("/mastery", response_model=MasteryResponseDTO)
def get_mastery(
    assignment_id: int,
    use_case: GetMasteryUseCase = Depends(dependencies.get_mastery_use_case),
) -> MasteryResponseDTO:
    return use_case.execute(assignment_id)


@router.get("/recommendations", response_model=RecommendationsResponseDTO)
def get_recommendations(
    assignment_id: int,
    use_case: GetRecommendationsUseCase = Depends(dependencies.get_recommendations_use_case),
) -> RecommendationsResponseDTO:
    return use_case.execute(assignment_id)


@router.get("/pre-training-statistics", response_model=PreTrainingStatisticsResponseDTO)
def get_pre_training_statistics(
    assignment_id: int,
    use_case: GetPreTrainingStatisticsUseCase = Depends(
        dependencies.get_pre_training_statistics_use_case
    ),
) -> PreTrainingStatisticsResponseDTO:
    return use_case.execute(assignment_id)
