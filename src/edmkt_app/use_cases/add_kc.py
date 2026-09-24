"""Adiciona um KC do professor + seus bindings (KC-02)."""

from __future__ import annotations

from pydantic import BaseModel

from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from api.shared.infrastructure.database.sqlite_connection import transaction
from edmkt_app.use_cases.base import BaseWriteUseCase
from edmkt_app.use_cases.kc_rules import revert_approval_if_approved


class AddKCDto(BaseModel):
    assignment_id: int
    name: str
    problem_ids: list[int] = []  # bindings opcionais; ints validados pelo DTO


class AddKCUseCase(BaseWriteUseCase):
    def _run(self, dto: AddKCDto) -> dict:
        with transaction(self._conn):
            # KC do professor nasce com kc_index NULL (não veio de um cluster do TCC — 05-01).
            kc_id = repos.KCRepository(self._conn).insert(
                models.KC(
                    id=None, assignment_id=dto.assignment_id, name=dto.name, kc_index=None
                )
            )
            repos.QMatrixRepository(self._conn).insert_bindings(
                dto.assignment_id, kc_id, dto.problem_ids
            )
            # Adicionar só PODE aumentar a cobertura → a guarda 0-KC não pode falhar aqui, mas a
            # edição ainda reverte uma aprovação (D-06).
            revert_approval_if_approved(self._conn, dto.assignment_id)
        return {"id": kc_id, "name": dto.name}
