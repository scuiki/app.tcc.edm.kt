"""O professor funde dois KCs: os problemas de drop_kc_id passam para keep_kc_id e drop some."""

from __future__ import annotations

from api.assignments.domain.assignment_repository import AssignmentRepository
from api.knowledge_components.application.edit_qmatrix_dto import (
    MergedKnowledgeComponentsDTO,
    MergeKnowledgeComponentsDTO,
)
from api.knowledge_components.domain.knowledge_component_repository import (
    KnowledgeComponentRepository,
)
from api.knowledge_components.domain.knowledge_components_are_distinct_rule import (
    KnowledgeComponentsAreDistinctRule,
)
from api.knowledge_components.domain.knowledge_components_belong_to_assignment_rule import (
    KnowledgeComponentsBelongToAssignmentRule,
)
from api.knowledge_components.domain.qmatrix_edit import (
    ensure_every_problem_keeps_a_kc,
    revert_approval_after_edit,
)
from api.knowledge_components.domain.qmatrix_repository import QMatrixRepository
from api.shared.application.unit_of_work import UnitOfWork
from api.shared.application.write_use_case import WriteUseCase
from api.shared.domain.business_rule import BusinessRule
from api.shared.domain.errors import NotFound


class MergeKnowledgeComponentsUseCase(WriteUseCase):
    def __init__(
        self,
        assignments: AssignmentRepository,
        knowledge_components: KnowledgeComponentRepository,
        qmatrix: QMatrixRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._knowledge_components = knowledge_components
        self._qmatrix = qmatrix
        self._unit_of_work = unit_of_work

    def rules(self) -> list[BusinessRule]:
        return [
            KnowledgeComponentsAreDistinctRule(),
            KnowledgeComponentsBelongToAssignmentRule(self._knowledge_components),
        ]

    def execute(self, dto: MergeKnowledgeComponentsDTO) -> MergedKnowledgeComponentsDTO:
        # A fusão consigo mesmo é recusada ANTES do 404: um mesmo id inexistente devolve 409, não
        # 404. Status code é contrato.
        if dto.keep_kc_id != dto.drop_kc_id and (
            self._knowledge_components.get(dto.keep_kc_id) is None
            or self._knowledge_components.get(dto.drop_kc_id) is None
        ):
            raise NotFound("KC inexistente")
        return super().execute(dto)

    def _run(self, dto: MergeKnowledgeComponentsDTO) -> MergedKnowledgeComponentsDTO:
        # A fusão é a união dos vínculos: só os problemas de drop_kc_id podem ficar sem KC.
        affected_problems = self._qmatrix.problems_of(dto.drop_kc_id)
        with self._unit_of_work:
            self._qmatrix.move_bindings(dto.assignment_id, dto.drop_kc_id, dto.keep_kc_id)
            self._knowledge_components.delete(dto.drop_kc_id)
            ensure_every_problem_keeps_a_kc(self._qmatrix, dto.assignment_id, affected_problems)
            revert_approval_after_edit(self._assignments, dto.assignment_id)
        return MergedKnowledgeComponentsDTO(keep_kc_id=dto.keep_kc_id, drop_kc_id=dto.drop_kc_id)
