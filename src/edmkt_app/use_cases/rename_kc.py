"""Renomeia um KC (KC-02). Não mexe na Q-matrix, então nenhum problema pode zerar."""

from __future__ import annotations

from pydantic import BaseModel

from edmkt_app.persistence import repositories as repos
from api.shared.infrastructure.database.sqlite_connection import transaction
from api.shared.domain.errors import NotFound
from edmkt_app.use_cases.base import BaseWriteUseCase
from edmkt_app.use_cases.kc_rules import revert_approval_if_approved


class RenameKCBody(BaseModel):
    """Só o que vem no corpo; o kc_id vem do path e é juntado no router."""

    name: str  # dado do professor: SQL parametrizado, nunca interpolado (T-05-11)


class RenameKCDto(BaseModel):
    kc_id: int
    name: str


class RenameKCUseCase(BaseWriteUseCase):
    def _run(self, dto: RenameKCDto) -> dict:
        kc_repo = repos.KCRepository(self._conn)
        kc = kc_repo.get(dto.kc_id)
        if kc is None:
            raise NotFound("KC inexistente")
        with transaction(self._conn):
            kc_repo.rename(dto.kc_id, dto.name)
            revert_approval_if_approved(self._conn, kc.assignment_id)
        return {"id": dto.kc_id, "name": dto.name}
