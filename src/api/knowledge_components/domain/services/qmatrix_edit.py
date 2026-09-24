# Duas consequências de editar a Q-matrix, avaliadas dentro da transação da própria edição.
from __future__ import annotations

from collections.abc import Iterable

from api.assignments.domain.entities.assignment_entity import AssignmentStatus
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.knowledge_components.domain.interfaces.qmatrix_repository import IQMatrixRepository
from api.shared.domain.errors.business_rule_violation import BusinessRuleViolation


def ensure_every_problem_keeps_a_kc(
    qmatrix: IQMatrixRepository, assignment_id: int, problem_ids: Iterable[int]
) -> None:
    # Recusa a edição se algum dos problemas afetados ficou com 0 KCs.
    for problem_id in problem_ids:
        if qmatrix.count_kcs_of_problem(assignment_id, problem_id) == 0:
            raise BusinessRuleViolation(
                [f"problema {problem_id} ficaria com 0 KCs — edição bloqueada"]
            )


def revert_approval_after_edit(assignments: IAssignmentRepository, assignment_id: int) -> None:
    # Editar uma Q-matrix aprovada devolve o assignment a rascunho, precisa aprovar de novo.
    assignment = assignments.get(assignment_id)
    if assignment is not None and assignment.status == AssignmentStatus.KC_APPROVED:
        assignments.set_status(assignment_id, AssignmentStatus.KC_DRAFT)
