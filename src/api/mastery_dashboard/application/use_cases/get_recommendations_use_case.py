"""As recomendações de reforço: os KCs de menor mastery primeiro, com texto em pt-BR e sem LLM."""

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.services.existing_assignment import get_existing_assignment
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.mastery_dashboard.application.dtos.mastery_dashboard_dto import (
    RecommendationsResponseDTO,
    ReinforcementRecommendationDTO,
)
from api.mastery_dashboard.application.services.published_model_mastery import PublishedModelMastery
from api.mastery_dashboard.domain.services.mastery_classification import (
    find_critical_knowledge_components,
)
from api.mastery_dashboard.domain.services.reinforcement_recommender import recommend_reinforcement


class GetRecommendationsUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        knowledge_components: IKnowledgeComponentRepository,
        mastery: PublishedModelMastery,
    ) -> None:
        self._assignments = assignments
        self._knowledge_components = knowledge_components
        self._mastery = mastery

    def execute(self, assignment_id: int) -> RecommendationsResponseDTO:
        assignment = get_existing_assignment(self._assignments, assignment_id)
        matrix, _model_info = self._mastery.of(assignment)
        names = {
            kc.id: kc.name for kc in self._knowledge_components.list_by_assignment(assignment_id)
        }
        kc_means = [
            (kc_id, names.get(kc_id, f"KC {kc_id}"), mean)
            for kc_id, mean in find_critical_knowledge_components(matrix)
        ]
        return RecommendationsResponseDTO(
            assignment_id=assignment_id,
            recommendations=[
                ReinforcementRecommendationDTO(
                    kc_id=r.kc_id, kc_name=r.kc_name, mean_mastery=r.mean_mastery, text=r.text
                )
                for r in recommend_reinforcement(kc_means)
            ],
        )
