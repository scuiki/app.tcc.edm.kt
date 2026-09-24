# A Q-matrix de um assignment vista pelos problemas, cada um com a descrição e os KCs que exige.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.services.existing_assignment import get_existing_assignment
from api.assignments.problems.domain.interfaces.problem_repository import IProblemRepository
from api.knowledge_components.application.dtos.edit_qmatrix_dto import KnowledgeComponentDTO
from api.knowledge_components.application.dtos.get_qmatrix_dto import (
    ProblemKnowledgeComponentsDTO,
    QMatrixResponseDTO,
)
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.qmatrix_repository import IQMatrixRepository


# Quem junta problema e KC é esta funcionalidade, a dona da Q-matrix e da FK para problem
class GetQMatrixUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        problems: IProblemRepository,
        knowledge_components: IKnowledgeComponentRepository,
        qmatrix: IQMatrixRepository,
    ) -> None:
        self._assignments = assignments
        self._problems = problems
        self._knowledge_components = knowledge_components
        self._qmatrix = qmatrix

    def execute(self, assignment_id: int) -> QMatrixResponseDTO:
        assignment = get_existing_assignment(self._assignments, assignment_id)
        name_of = {
            kc.id: kc.name for kc in self._knowledge_components.list_by_assignment(assignment_id)
        }
        kcs_of: dict[int, list[int]] = {}
        for binding in self._qmatrix.list_by_assignment(assignment_id):
            kcs_of.setdefault(binding.problem_id, []).append(binding.kc_id)
        return QMatrixResponseDTO(
            assignment_id=assignment_id,
            status=assignment.status,
            problems=[
                ProblemKnowledgeComponentsDTO(
                    problem_id=problem.problem_id,
                    description=problem.description,
                    knowledge_components=[
                        KnowledgeComponentDTO(id=kc_id, name=name_of[kc_id])
                        for kc_id in sorted(kcs_of.get(problem.problem_id, []))
                    ],
                )
                for problem in self._problems.list_by_assignment(assignment_id)
            ],
        )
