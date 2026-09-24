# O professor liga um KC que já existe a mais um problema, o caminho de volta do xis do chip.

from __future__ import annotations

from dataclasses import dataclass

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.problems.domain.interfaces.problem_repository import IProblemRepository
from api.knowledge_components.application.dtos.edit_knowledge_components_dto import (
    ProblemKnowledgeComponentDTO,
)
from api.knowledge_components.domain.entities.problem_knowledge_component_entity import (
    ProblemKnowledgeComponent,
)
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)
from api.knowledge_components.domain.rules.knowledge_component_not_linked_yet_rule import (
    KnowledgeComponentNotLinkedYetRule,
)
from api.knowledge_components.domain.rules.problems_belong_to_assignment_rule import (
    ProblemsBelongToAssignmentRule,
)
from api.knowledge_components.domain.services.active_knowledge_component import (
    get_active_knowledge_component,
)
from api.knowledge_components.domain.services.knowledge_component_edit import (
    revert_approval_after_edit,
)
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.interfaces.business_rule import IBusinessRule


# O pedido com o assignment do KC, que é o que as regras precisam conferir
@dataclass(frozen=True)
class _LinkRequest:
    assignment_id: int
    kc_id: int
    problem_id: int

    @property
    def problem_ids(self) -> list[int]:
        return [self.problem_id]


class AddProblemKnowledgeComponentUseCase(WriteUseCase):
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
            ProblemsBelongToAssignmentRule(self._problems),
            KnowledgeComponentNotLinkedYetRule(self._problem_kcs),
        ]

    def execute(self, dto: ProblemKnowledgeComponentDTO) -> ProblemKnowledgeComponentDTO:
        knowledge_component = get_active_knowledge_component(
            self._knowledge_components, self._assignments, dto.kc_id
        )
        return super().execute(
            _LinkRequest(knowledge_component.assignment_id, dto.kc_id, dto.problem_id)
        )

    def _run(self, request: _LinkRequest) -> ProblemKnowledgeComponentDTO:
        with self._unit_of_work:
            self._problem_kcs.add(
                ProblemKnowledgeComponent(
                    id=None,
                    assignment_id=request.assignment_id,
                    kc_id=request.kc_id,
                    problem_id=request.problem_id,
                )
            )
            revert_approval_after_edit(self._assignments, request.assignment_id)
        return ProblemKnowledgeComponentDTO(kc_id=request.kc_id, problem_id=request.problem_id)
