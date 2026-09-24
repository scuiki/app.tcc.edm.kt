# Os KCs de um assignment, cada um com os problemas ligados a ele pela Q-matrix.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.services.existing_assignment import get_existing_assignment
from api.knowledge_components.application.dtos.list_knowledge_components_dto import (
    KnowledgeComponentWithProblemsDTO,
    ListKnowledgeComponentsResponseDTO,
)
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.qmatrix_repository import IQMatrixRepository


class ListKnowledgeComponentsUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        knowledge_components: IKnowledgeComponentRepository,
        qmatrix: IQMatrixRepository,
    ) -> None:
        self._assignments = assignments
        self._knowledge_components = knowledge_components
        self._qmatrix = qmatrix

    def execute(self, assignment_id: int) -> ListKnowledgeComponentsResponseDTO:
        get_existing_assignment(self._assignments, assignment_id)
        problems_of: dict[int, list[int]] = {}
        for binding in self._qmatrix.list_by_assignment(assignment_id):
            problems_of.setdefault(binding.kc_id, []).append(binding.problem_id)
        return ListKnowledgeComponentsResponseDTO(
            assignment_id=assignment_id,
            knowledge_components=[
                KnowledgeComponentWithProblemsDTO(
                    id=kc.id, name=kc.name, problem_ids=sorted(problems_of.get(kc.id, []))
                )
                for kc in self._knowledge_components.list_by_assignment(assignment_id)
            ],
        )
