# Renomear um KC não mexe nos vínculos com os problemas, então nenhum problema fica sem KC.
from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.knowledge_components.application.dtos.edit_knowledge_components_dto import (
    KnowledgeComponentDTO,
    RenameKnowledgeComponentDTO,
)
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.services.active_knowledge_component import (
    get_active_knowledge_component,
)
from api.knowledge_components.domain.services.knowledge_component_edit import (
    revert_approval_after_edit,
)
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.use_cases.write_use_case import WriteUseCase


class RenameKnowledgeComponentUseCase(WriteUseCase):
    def __init__(
        self,
        assignments: IAssignmentRepository,
        knowledge_components: IKnowledgeComponentRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._knowledge_components = knowledge_components
        self._unit_of_work = unit_of_work

    def _run(self, dto: RenameKnowledgeComponentDTO) -> KnowledgeComponentDTO:
        knowledge_component = get_active_knowledge_component(
            self._knowledge_components, self._assignments, dto.kc_id
        )
        with self._unit_of_work:
            self._knowledge_components.rename(dto.kc_id, dto.name)
            revert_approval_after_edit(self._assignments, knowledge_component.assignment_id)
        return KnowledgeComponentDTO(id=dto.kc_id, name=dto.name)
