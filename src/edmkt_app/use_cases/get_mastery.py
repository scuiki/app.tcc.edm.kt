"""Matriz aluno×KC + KCs críticos + alunos em atenção (DASH-01/02/03/05)."""

from __future__ import annotations

import sqlite3

from edmkt_core.mastery import at_risk_students, critical_kcs

from edmkt_app.use_cases.base import require_assignment
from edmkt_app.use_cases.uncertainty_frame import uncertainty_frame


class GetMasteryUseCase:
    """Leitura: não estende BaseWriteUseCase — não há regra a validar antes de ler."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, assignment_id: int) -> dict:
        assignment = require_assignment(self._conn, assignment_id)
        matrix, first_auc, trained_at = uncertainty_frame(self._conn, assignment)
        return {
            "assignment_id": assignment_id,
            "first_auc": first_auc,  # DASH-05/D-08: moldura sempre presente
            "trained_at": trained_at,
            # a matriz interna é chaveada por tupla; achatada aqui para o payload JSON
            "matrix": [
                {"subject_id": subject_id, "kc_id": kc_id, "mastery": mastery}
                for (subject_id, kc_id), mastery in matrix.items()
            ],
            "critical_kcs": [
                {"kc_id": kc_id, "mean_mastery": mean} for kc_id, mean in critical_kcs(matrix)
            ],
            "at_risk_students": at_risk_students(matrix),
        }
