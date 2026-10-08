# O professor aprova os KCs que o LLM rascunhou, é o único caminho que libera o treino.
from __future__ import annotations

from api.assignments.domain.value_objects.assignment_status import AssignmentStatus
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.services.existing_assignment import get_existing_assignment
from api.assignments.problems.domain.interfaces.problem_repository import IProblemRepository
from api.knowledge_components.application.dtos.edit_knowledge_components_dto import (
    ApprovedKnowledgeComponentsDTO,
    ApproveKnowledgeComponentsDTO,
)
from api.knowledge_components.domain.rules.assignment_has_knowledge_components_rule import (
    AssignmentHasKnowledgeComponentsRule,
)
from api.knowledge_components.domain.rules.assignment_is_kc_draft_rule import (
    AssignmentIsKcDraftRule,
)
from api.knowledge_components.domain.rules.every_problem_has_a_knowledge_component_rule import (
    EveryProblemHasAKnowledgeComponentRule,
)
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.interfaces.business_rule import IBusinessRule


class ApproveKnowledgeComponentsUseCase(WriteUseCase):
    def __init__(
        self,
        assignments: IAssignmentRepository,
        problems: IProblemRepository,
        knowledge_components: IKnowledgeComponentRepository,
        problem_kcs: IProblemKnowledgeComponentRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._problems = problems
        self._knowledge_components = knowledge_components
        self._problem_kcs = problem_kcs
        self._unit_of_work = unit_of_work

    def rules(self) -> list[IBusinessRule]:
        return [
            AssignmentIsKcDraftRule(self._assignments),
            AssignmentHasKnowledgeComponentsRule(self._knowledge_components),
            EveryProblemHasAKnowledgeComponentRule(
                self._problems, self._knowledge_components, self._problem_kcs
            ),
        ]

    def execute(self, dto: ApproveKnowledgeComponentsDTO) -> ApprovedKnowledgeComponentsDTO:
        # A inexistência é 404 e não entra no acúmulo, sem alvo não há regra a aplicar.
        get_existing_assignment(self._assignments, dto.assignment_id)
        return super().execute(dto)

    def _run(self, dto: ApproveKnowledgeComponentsDTO) -> ApprovedKnowledgeComponentsDTO:
        with self._unit_of_work:
            self._assignments.set_status(dto.assignment_id, AssignmentStatus.KC_APPROVED)
        return ApprovedKnowledgeComponentsDTO(assignment_id=dto.assignment_id, status=AssignmentStatus.KC_APPROVED)
