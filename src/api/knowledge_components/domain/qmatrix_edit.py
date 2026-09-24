"""As duas consequências de editar a Q-matrix, avaliadas DENTRO da transação da edição.

Não são regras de antes da edição: "nenhum problema ficou sem KC" só pode ser conferido depois da
mudança, e reverter a aprovação é efeito, não validação. Levantar dentro do `with unit_of_work` é o
que desfaz a edição inteira.
"""

from __future__ import annotations

from collections.abc import Iterable

from api.assignments.domain.assignment_entity import AssignmentStatus
from api.assignments.domain.assignment_repository import AssignmentRepository
from api.knowledge_components.domain.qmatrix_repository import QMatrixRepository
from api.shared.domain.errors import BusinessRuleViolation


def ensure_every_problem_keeps_a_kc(
    qmatrix: QMatrixRepository, assignment_id: int, problem_ids: Iterable[int]
) -> None:
    """Recusa a edição se algum dos problemas afetados ficou com 0 KCs."""
    for problem_id in problem_ids:
        if qmatrix.count_kcs_of_problem(assignment_id, problem_id) == 0:
            raise BusinessRuleViolation(
                [f"problema {problem_id} ficaria com 0 KCs — edição bloqueada"]
            )


def revert_approval_after_edit(assignments: AssignmentRepository, assignment_id: int) -> None:
    """Editar uma Q-matrix aprovada a devolve a rascunho: o professor precisa aprovar de novo."""
    assignment = assignments.get(assignment_id)
    if assignment is not None and assignment.status == AssignmentStatus.KC_APPROVED:
        assignments.set_status(assignment_id, AssignmentStatus.KC_DRAFT)
