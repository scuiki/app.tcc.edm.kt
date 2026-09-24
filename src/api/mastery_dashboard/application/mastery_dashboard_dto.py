"""As respostas de /mastery-dashboard/{assignment_id}/..."""

from __future__ import annotations

from pydantic import BaseModel


class StudentMasteryDTO(BaseModel):
    student_id: str
    kc_id: int
    mastery: float


class CriticalKnowledgeComponentDTO(BaseModel):
    kc_id: int
    mean_mastery: float


class MasteryResponseDTO(BaseModel):
    assignment_id: int
    # TrainedModelInfo: sempre presente; None quando não há modelo publicado
    first_attempt_auc: float | None
    trained_at: str | None
    matrix: list[StudentMasteryDTO]
    critical_kcs: list[CriticalKnowledgeComponentDTO]  # do mais fraco ao mais forte
    students_at_risk: list[str]  # student_ids


class ReinforcementRecommendationDTO(BaseModel):
    kc_id: int
    kc_name: str
    mean_mastery: float
    text: str


class RecommendationsResponseDTO(BaseModel):
    assignment_id: int
    recommendations: list[ReinforcementRecommendationDTO]


class PreTrainingStatisticsResponseDTO(BaseModel):
    assignment_id: int
    success_rate: dict[int, float]
    learning_curve: dict[int, float]
    compile_error_rate: dict[int, float]
