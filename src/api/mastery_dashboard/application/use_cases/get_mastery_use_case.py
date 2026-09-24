# A matriz aluno × KC, os KCs críticos e os alunos em risco, com o TrainedModelInfo junto.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.services.existing_assignment import get_existing_assignment
from api.mastery_dashboard.application.dtos.mastery_dashboard_dto import (
    CriticalKnowledgeComponentDTO,
    MasteryResponseDTO,
    StudentMasteryDTO,
)
from api.mastery_dashboard.application.services.published_model_mastery import PublishedModelMastery
from api.mastery_dashboard.domain.services.mastery_classification import (
    find_critical_knowledge_components,
    find_students_at_risk,
)


class GetMasteryUseCase:
    def __init__(self, assignments: IAssignmentRepository, mastery: PublishedModelMastery) -> None:
        self._assignments = assignments
        self._mastery = mastery

    def execute(self, assignment_id: int) -> MasteryResponseDTO:
        assignment = get_existing_assignment(self._assignments, assignment_id)
        matrix, model_info = self._mastery.of(assignment)
        return MasteryResponseDTO(
            assignment_id=assignment_id,
            first_attempt_auc=model_info.first_attempt_auc,
            trained_at=model_info.trained_at,
            matrix=[
                StudentMasteryDTO(student_id=student_id, kc_id=kc_id, mastery=mastery)
                for (student_id, kc_id), mastery in matrix.items()
            ],
            critical_kcs=[
                CriticalKnowledgeComponentDTO(kc_id=kc_id, mean_mastery=mean)
                for kc_id, mean in find_critical_knowledge_components(matrix)
            ],
            students_at_risk=find_students_at_risk(matrix),
        )
