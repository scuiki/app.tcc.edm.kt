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
    refuse_edit_after_training,
    revert_approval_after_edit,
)
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.services.clock import utc_now_iso
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
            refuse_edit_after_training(self._assignments, knowledge_component.assignment_id)
            # O mesmo nome não é edição, então não tira as estrelas nem reabre a aprovação
            if dto.name != knowledge_component.name:
                knowledge_component.name = dto.name
                knowledge_component.updated_at = utc_now_iso()
                self._knowledge_components.rename(
                    dto.kc_id, knowledge_component.name, knowledge_component.updated_at
                )
                revert_approval_after_edit(self._assignments, knowledge_component.assignment_id)
        return KnowledgeComponentDTO(
            id=dto.kc_id,
            name=knowledge_component.name,
            is_generated_by_llm=knowledge_component.is_generated_by_llm,
        )
