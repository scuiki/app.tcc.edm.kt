"""Specifications: uma regra de negócio nomeada por classe, testável fora de HTTP.

Cada uma devolve a MENSAGEM de recusa ou None. Elas rodam todas (base.BaseWriteUseCase agrega),
então cada uma busca o que precisa e tolera ausência — nenhuma pode assumir que outra passou.

Contrato preservado ao pé da letra: as mensagens e a granularidade das recusas são as dos
routers de hoje, porque texto e status code são contrato. Onde o código atual CONFLATA
"assignment inexistente" com "status errado" num 409 só, a spec conflata igual — está marcado
abaixo como herdado, não como desenho.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from api.assignments.infrastructure.sqlite_assignment_repository import SqliteAssignmentRepository


@dataclass(frozen=True)
class AssignmentInStatus:
    """O assignment existe E está num dos status permitidos.

    HERDADO (não desenho): assignment inexistente devolve a MESMA mensagem de status errado,
    porque é o que /training e /kc/generate fazem hoje — os dois viram 409. Separar daria 404
    para um id inexistente, o que é mais correto e é mudança de contrato; fica anotado para
    ser decidido à parte.
    """

    allowed: tuple[str, ...]
    message: str

    def check(self, conn: sqlite3.Connection, dto) -> str | None:
        assignment = SqliteAssignmentRepository(conn).get(dto.assignment_id)
        if assignment is None or assignment.status not in self.allowed:
            return self.message
        return None
