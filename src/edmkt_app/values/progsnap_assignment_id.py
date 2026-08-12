"""AssignmentID do ProgSnap2 — o id do DATASET, distinto do id do banco (backlog 999.2)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProgSnapAssignmentId:
    """AssignmentID do ProgSnap2 — o id do DATASET, não o id do banco.

    Os dois são inteiros e significam coisas diferentes; confundi-los custou uma consulta manual
    ao app.db na UAT da Fase 4 (backlog 999.2). Como tipo distinto, passar um no lugar do outro
    para de ser um int que passa despercebido.
    """

    value: int

    @classmethod
    def from_name(cls, assignment_name: str) -> "ProgSnapAssignmentId":
        m = re.search(r"(\d+)", assignment_name)
        if m is None:
            raise ValueError(f"AssignmentID não derivável do nome: {assignment_name!r}")
        return cls(int(m.group(1)))

    def __str__(self) -> str:
        return str(self.value)
