# O professor tira um KC de um problema só, o xis do chip, sem deixar o problema sem KC.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.knowledge_components.application.dtos.edit_knowledge_components_dto import (
    ProblemKnowledgeComponentDTO,
    RemovedProblemKnowledgeComponentDTO,
)
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)
from api.knowledge_components.domain.services.active_knowledge_component import (
    get_active_knowledge_component,
)
from api.knowledge_components.domain.services.knowledge_component_edit import (
    ensure_every_problem_keeps_a_kc,
    revert_approval_after_edit,
)
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.services.clock import utc_now_iso
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.errors.not_found import NotFound


class RemoveProblemKnowledgeComponentUseCase(WriteUseCase):
    def __init__(
        self,
        assignments: IAssignmentRepository,
        knowledge_components: IKnowledgeComponentRepository,
        problem_kcs: IProblemKnowledgeComponentRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._knowledge_components = knowledge_components
        self._problem_kcs = problem_kcs
        self._unit_of_work = unit_of_work

    def _run(self, dto: ProblemKnowledgeComponentDTO) -> RemovedProblemKnowledgeComponentDTO:
        knowledge_component = get_active_knowledge_component(
            self._knowledge_components, self._assignments, dto.kc_id
        )
        assignment_id = knowledge_component.assignment_id
        removed_at = utc_now_iso()
        with self._unit_of_work:
            if not self._problem_kcs.remove(assignment_id, dto.kc_id, dto.problem_id, removed_at):
                raise NotFound("o KC não está ligado a esse problema")
            # Levanta dentro da transação, o que desfaz a remoção
            ensure_every_problem_keeps_a_kc(self._problem_kcs, assignment_id, [dto.problem_id])
            # Um KC sem nenhum problema não entra em nada, então sai junto
            knowledge_component_removed = not self._problem_kcs.problems_of(dto.kc_id)
            if knowledge_component_removed:
                self._knowledge_components.remove(dto.kc_id, removed_at)
            revert_approval_after_edit(self._assignments, assignment_id)
        return RemovedProblemKnowledgeComponentDTO(
            kc_id=dto.kc_id,
            problem_id=dto.problem_id,
            knowledge_component_removed=knowledge_component_removed,
        )
