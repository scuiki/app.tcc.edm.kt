"""O professor renomeia um KC. Não mexe na Q-matrix, então nenhum problema pode ficar sem KC."""

from __future__ import annotations

from api.assignments.domain.assignment_repository import AssignmentRepository
from api.knowledge_components.application.edit_qmatrix_dto import (
    KnowledgeComponentDTO,
    RenameKnowledgeComponentDTO,
)
from api.knowledge_components.domain.knowledge_component_repository import (
    KnowledgeComponentRepository,
)
from api.knowledge_components.domain.qmatrix_edit import revert_approval_after_edit
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.errors.not_found import NotFound


class RenameKnowledgeComponentUseCase(WriteUseCase):
    def __init__(
        self,
        assignments: AssignmentRepository,
        knowledge_components: KnowledgeComponentRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._knowledge_components = knowledge_components
        self._unit_of_work = unit_of_work

    def _run(self, dto: RenameKnowledgeComponentDTO) -> KnowledgeComponentDTO:
        knowledge_component = self._knowledge_components.get(dto.kc_id)
        if knowledge_component is None:
            raise NotFound("KC inexistente")
        with self._unit_of_work:
            self._knowledge_components.rename(dto.kc_id, dto.name)
            revert_approval_after_edit(self._assignments, knowledge_component.assignment_id)
        return KnowledgeComponentDTO(id=dto.kc_id, name=dto.name)
