# O professor adiciona um KC, já ligado aos problemas que escolher.
from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.problems.domain.interfaces.problem_repository import IProblemRepository
from api.knowledge_components.application.dtos.edit_knowledge_components_dto import (
    AddKnowledgeComponentDTO,
    KnowledgeComponentDTO,
)
from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.rules.problems_belong_to_assignment_rule import (
    ProblemsBelongToAssignmentRule,
)
from api.knowledge_components.domain.services.knowledge_component_edit import (
    revert_approval_after_edit,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.interfaces.business_rule import IBusinessRule


class AddKnowledgeComponentUseCase(WriteUseCase):
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
        return [ProblemsBelongToAssignmentRule(self._problems)]

    def _run(self, dto: AddKnowledgeComponentDTO) -> KnowledgeComponentDTO:
        with self._unit_of_work:
            # Um KC do professor não veio de um grupo do KCGen-KT, group_index fica vazio.
            kc_id = self._knowledge_components.add(
                KnowledgeComponent(id=None, assignment_id=dto.assignment_id, name=dto.name)
            )
            self._problem_kcs.bind_problems(dto.assignment_id, kc_id, dto.problem_ids)
            # Toda edição volta os KCs aprovados para rascunho, mesmo esta que só cobre mais.
            revert_approval_after_edit(self._assignments, dto.assignment_id)
        return KnowledgeComponentDTO(id=kc_id, name=dto.name)
