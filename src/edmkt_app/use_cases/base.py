"""TRANSITÓRIO: a base dos use cases que ainda recebem `conn` (os que não migraram para api/).

A base nova é api/shared/application/write_use_case.py. Esta some quando o último use case migrar.

Base dos use cases de escrita: validar tudo, depois agir.

O runner de specifications roda a lista INTEIRA e agrega — sem short-circuit. Um payload com
três problemas devolve os três, em vez de obrigar o professor a descobrir um por vez.

Contrato que isso impõe a quem escreve uma spec: **ela não pode assumir que outra passou**.
Como todas rodam, uma spec que dependa de "o assignment existe" tem de buscar o assignment ela
mesma e tolerar ausência, senão o segundo item da lista estoura com AttributeError enquanto o
primeiro tentava reportar exatamente que ele não existe.

`BusinessRuleViolation` é da app layer e não conhece HTTP: quem traduz para status code é o router.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Protocol

from api.shared.domain.errors import BusinessRuleViolation, NotFound
from api.assignments.infrastructure.sqlite_assignment_repository import SqliteAssignmentRepository
from api.assignments.domain.assignment_entity import Assignment


class Specification(Protocol):
    """Devolve a mensagem de recusa, ou None se a regra passa."""

    def check(self, conn: sqlite3.Connection, dto: Any) -> str | None: ...


def require_assignment(conn: sqlite3.Connection, assignment_id: int) -> Assignment:
    """O assignment alvo, ou NotFound — o 404 que todo use case sobre um assignment começa por."""
    assignment = SqliteAssignmentRepository(conn).get(assignment_id)
    if assignment is None:
        raise NotFound("assignment inexistente")
    return assignment


class BaseWriteUseCase:
    """Use case que MUDA estado (create/update/delete). Leitura não estende esta base.

    A conexão vem no construtor porque ela é por-requisição (api/deps.get_conn) — o use case
    nasce e morre com a requisição, e os repositórios são casca fina sobre ela.
    """

    specs: list[Specification] = []

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def validate(self, dto: Any) -> None:
        errors = [
            message
            for spec in self.specs
            if (message := spec.check(self._conn, dto)) is not None
        ]
        if errors:
            raise BusinessRuleViolation(errors)

    def execute(self, dto: Any) -> Any:
        self.validate(dto)
        return self._run(dto)

    def _run(self, dto: Any) -> Any:
        raise NotImplementedError
