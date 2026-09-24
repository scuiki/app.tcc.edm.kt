"""O professor adiciona um KC, já ligado aos problemas que escolher."""

from __future__ import annotations

from api.assignments.domain.assignment_repository import AssignmentRepository
from api.knowledge_components.application.edit_qmatrix_dto import (
    AddKnowledgeComponentDTO,
    KnowledgeComponentDTO,
)
from api.knowledge_components.domain.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.knowledge_component_repository import (
    KnowledgeComponentRepository,
)
from api.knowledge_components.domain.qmatrix_edit import revert_approval_after_edit
from api.knowledge_components.domain.qmatrix_repository import QMatrixRepository
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.use_cases.write_use_case import WriteUseCase


class AddKnowledgeComponentUseCase(WriteUseCase):
    def __init__(
        self,
        assignments: AssignmentRepository,
        knowledge_components: KnowledgeComponentRepository,
        qmatrix: QMatrixRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._knowledge_components = knowledge_components
        self._qmatrix = qmatrix
        self._unit_of_work = unit_of_work

    def _run(self, dto: AddKnowledgeComponentDTO) -> KnowledgeComponentDTO:
        with self._unit_of_work:
            # Um KC do professor não veio de um grupo do KCGen-KT: group_index fica vazio.
            kc_id = self._knowledge_components.add(
                KnowledgeComponent(id=None, assignment_id=dto.assignment_id, name=dto.name)
            )
            self._qmatrix.bind_problems(dto.assignment_id, kc_id, dto.problem_ids)
            # Adicionar só aumenta a cobertura, então nenhum problema pode ficar sem KC; mas a
            # edição ainda devolve uma Q-matrix aprovada a rascunho.
            revert_approval_after_edit(self._assignments, dto.assignment_id)
        return KnowledgeComponentDTO(id=kc_id, name=dto.name)
