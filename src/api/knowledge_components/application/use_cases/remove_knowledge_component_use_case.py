# O professor remove um KC e seus vínculos, desde que nenhum problema fique sem KC.
from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.knowledge_components.application.dtos.edit_knowledge_components_dto import (
    RemovedKnowledgeComponentDTO,
    RemoveKnowledgeComponentDTO,
)
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.services.knowledge_component_edit import (
    ensure_every_problem_keeps_a_kc,
    revert_approval_after_edit,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.services.clock import utc_now_iso
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.errors.not_found import NotFound


class RemoveKnowledgeComponentUseCase(WriteUseCase):
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

    def _run(self, dto: RemoveKnowledgeComponentDTO) -> RemovedKnowledgeComponentDTO:
        knowledge_component = self._knowledge_components.get(dto.kc_id)
        if knowledge_component is None:
            raise NotFound("KC inexistente")
        # Problemas que este KC liga, colhidos antes de remover, só eles podem ficar sem KC.
        affected_problems = self._problem_kcs.problems_of(dto.kc_id)
        removed_at = utc_now_iso()
        with self._unit_of_work:
            self._problem_kcs.remove_all_of(dto.kc_id, removed_at)
            self._knowledge_components.remove(dto.kc_id, removed_at)
            ensure_every_problem_keeps_a_kc(
                self._problem_kcs, knowledge_component.assignment_id, affected_problems
            )  # levanta dentro da transação, o que desfaz a remoção
            revert_approval_after_edit(self._assignments, knowledge_component.assignment_id)
        return RemovedKnowledgeComponentDTO(deleted_kc_id=dto.kc_id)
