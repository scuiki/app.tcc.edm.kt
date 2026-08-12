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

from edmkt_app.persistence import repositories as repos


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
        assignment = repos.AssignmentRepository(conn).get(dto.assignment_id)
        if assignment is None or assignment.status not in self.allowed:
            return self.message
        return None


@dataclass(frozen=True)
class AssignmentIsDraft:
    """Só se aprova um rascunho de fato (WR-02): aprovar fora de kc_draft deixaria o treino
    rodar sobre uma Q-matrix inexistente, burlando o gate humano."""

    def check(self, conn: sqlite3.Connection, dto) -> str | None:
        assignment = repos.AssignmentRepository(conn).get(dto.assignment_id)
        if assignment is None:
            return None  # inexistência é NotFound, levantado antes — aqui não é regra violada
        if assignment.status != "kc_draft":
            return f"assignment não está em kc_draft (status atual: {assignment.status})"
        return None


@dataclass(frozen=True)
class AssignmentHasKCs:
    """Um kc_draft vazio não tem Q-matrix a treinar (KC-04)."""

    def check(self, conn: sqlite3.Connection, dto) -> str | None:
        if not repos.KCRepository(conn).list_by_assignment(dto.assignment_id):
            return "assignment não tem nenhum KC para aprovar"
        return None


@dataclass(frozen=True)
class KCsAreDistinct:
    """Auto-merge não faz sentido (CR-02): recusa explícita em vez de depender do rollback."""

    def check(self, conn: sqlite3.Connection, dto) -> str | None:
        if dto.kc_keep == dto.kc_drop:
            return "kc_keep e kc_drop são o mesmo KC"
        return None


@dataclass(frozen=True)
class KCsBelongToAssignment:
    """Autorização (CR-02): sem isto, o delete de kc_drop apagaria um KC de OUTRO assignment
    (o DELETE não filtra por assignment), deixando FK pendurada na qmatrix alheia."""

    def check(self, conn: sqlite3.Connection, dto) -> str | None:
        kc_repo = repos.KCRepository(conn)
        keep, drop = kc_repo.get(dto.kc_keep), kc_repo.get(dto.kc_drop)
        if keep is None or drop is None:
            return None  # inexistência é NotFound, levantado antes
        if keep.assignment_id != dto.assignment_id or drop.assignment_id != dto.assignment_id:
            return "KC não pertence ao assignment"
        return None
