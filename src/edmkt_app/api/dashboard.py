"""Router /dashboard — HTTP puro sobre os use cases de leitura (DASH-01..05, REC-01, 999.2).

Toda rota é GET. O único write do slice é a materialização lazy compute-once da matriz de
mastery, que vive em mastery_service (T-06-15) e é alcançada pelo use case, não daqui.

Moldura de incerteza (DASH-05/D-08): TODA resposta de mastery carrega first_auc + trained_at —
nunca um veredito cru. Sem modelo publicado a moldura vem nula e a matriz vazia, e ainda assim
é resposta enquadrada, não 404. A regra vive em use_cases/uncertainty_frame.py.

Segurança: ids são int (path param, V5); os caminhos de FS saem de int IDs + value objects
internos (modeling_frame / eda), nunca de caminho de cliente (T-06-12); todo SQL é
parametrizado pelos repositórios (T-06-13).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from edmkt_app.api.deps import (
    get_eda_uc,
    get_mastery_uc,
    get_recommendations_uc,
)
from edmkt_app.use_cases.get_eda import GetEdaUseCase
from edmkt_app.use_cases.get_mastery import GetMasteryUseCase
from edmkt_app.use_cases.get_recommendations import GetRecommendationsUseCase

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/mastery/{assignment_id}")
def get_mastery(assignment_id: int, uc: GetMasteryUseCase = Depends(get_mastery_uc)) -> dict:
    return uc.execute(assignment_id)


@router.get("/dashboard/eda/{assignment_id}")
def get_eda(assignment_id: int, uc: GetEdaUseCase = Depends(get_eda_uc)) -> dict:
    return uc.execute(assignment_id)


@router.get("/dashboard/recommendations/{assignment_id}")
def get_recommendations(
    assignment_id: int, uc: GetRecommendationsUseCase = Depends(get_recommendations_uc)
) -> dict:
    return uc.execute(assignment_id)
