# O KC alvo de um pedido por kc_id, ou NotFound, também quando a turma ou o assignment dele saiu.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.shared.domain.errors.not_found import NotFound


def get_active_knowledge_component(
    knowledge_components: IKnowledgeComponentRepository,
    assignments: IAssignmentRepository,
    kc_id: int,
) -> KnowledgeComponent:
    knowledge_component = knowledge_components.get(kc_id)
    # O repositório de assignments ignora os excluídos, e o KC deles sai junto
    if knowledge_component is None or assignments.get(knowledge_component.assignment_id) is None:
        raise NotFound("KC inexistente")
    return knowledge_component
