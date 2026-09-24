"""O professor remove um KC e seus vínculos, desde que nenhum problema fique sem KC."""

from __future__ import annotations

from api.assignments.domain.assignment_repository import AssignmentRepository
from api.knowledge_components.application.edit_qmatrix_dto import (
    RemovedKnowledgeComponentDTO,
    RemoveKnowledgeComponentDTO,
)
from api.knowledge_components.domain.knowledge_component_repository import (
    KnowledgeComponentRepository,
)
from api.knowledge_components.domain.qmatrix_edit import (
    ensure_every_problem_keeps_a_kc,
    revert_approval_after_edit,
)
from api.knowledge_components.domain.qmatrix_repository import QMatrixRepository
from api.shared.application.unit_of_work import UnitOfWork
from api.shared.application.write_use_case import WriteUseCase
from api.shared.domain.errors import NotFound


class RemoveKnowledgeComponentUseCase(WriteUseCase):
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

    def _run(self, dto: RemoveKnowledgeComponentDTO) -> RemovedKnowledgeComponentDTO:
        knowledge_component = self._knowledge_components.get(dto.kc_id)
        if knowledge_component is None:
            raise NotFound("KC inexistente")
        # Os problemas que este KC liga, colhidos ANTES de remover: só eles podem ficar sem KC.
        affected_problems = self._qmatrix.problems_of(dto.kc_id)
        with self._unit_of_work:
            self._qmatrix.delete_bindings_of(dto.kc_id)
            self._knowledge_components.delete(dto.kc_id)
            ensure_every_problem_keeps_a_kc(
                self._qmatrix, knowledge_component.assignment_id, affected_problems
            )  # levanta dentro da transação: desfaz a remoção
            revert_approval_after_edit(self._assignments, knowledge_component.assignment_id)
        return RemovedKnowledgeComponentDTO(deleted_kc_id=dto.kc_id)
