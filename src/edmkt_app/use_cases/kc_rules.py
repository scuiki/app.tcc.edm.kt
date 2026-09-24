"""Regras de Q-matrix que rodam DENTRO da transação — por isso não são specifications.

Uma specification decide antes de agir. Estas duas só podem ser avaliadas depois da mutação:
a guarda 0-KC precisa ver o estado já editado para saber se algum problema ficou órfão, e a
reversão de aprovação é efeito, não validação. Levantar aqui dentro do `with transaction` é o
que faz o ROLLBACK acontecer (D-07).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from api.shared.domain.errors import BusinessRuleViolation
from edmkt_app.persistence import repositories as repos


def assert_no_empty_problem(
    conn: sqlite3.Connection, assignment_id: int, problems: Iterable[int]
) -> None:
    qrepo = repos.QMatrixRepository(conn)
    for problem_id in problems:
        if qrepo.kc_count_for_problem(assignment_id, problem_id) == 0:
            # Levantada DENTRO da transação: a exceção é o que faz o ROLLBACK da edição.
            raise BusinessRuleViolation(
                [f"problema {problem_id} ficaria com 0 KCs — edição bloqueada (D-07)"]
            )


def revert_approval_if_approved(conn: sqlite3.Connection, assignment_id: int) -> None:
    # D-06: editar a Q-matrix após aprovar reverte kc_approved → kc_draft (re-aprovação exigida).
    arepo = repos.AssignmentRepository(conn)
    assignment = arepo.get(assignment_id)
    if assignment is not None and assignment.status == "kc_approved":
        arepo.set_status(assignment_id, "kc_draft")
