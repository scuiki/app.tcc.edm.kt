"""Remove um KC e seus bindings (KC-02), com a guarda 0-KC dentro da transação (D-07)."""

from __future__ import annotations

from pydantic import BaseModel

from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence import transaction
from edmkt_app.use_cases.base import BaseWriteUseCase, NotFound
from edmkt_app.use_cases.kc_rules import assert_no_empty_problem, revert_approval_if_approved


class RemoveKCDto(BaseModel):
    kc_id: int


class RemoveKCUseCase(BaseWriteUseCase):
    def _run(self, dto: RemoveKCDto) -> dict:
        kc_repo = repos.KCRepository(self._conn)
        qmatrix_repo = repos.QMatrixRepository(self._conn)
        kc = kc_repo.get(dto.kc_id)
        if kc is None:
            raise NotFound("KC inexistente")
        # Colhe os problemas que este KC liga ANTES de remover — só eles podem zerar (D-07).
        affected = qmatrix_repo.problems_of_kc(dto.kc_id)
        with transaction(self._conn):
            qmatrix_repo.delete_by_kc(dto.kc_id)
            kc_repo.delete(dto.kc_id)
            assert_no_empty_problem(self._conn, kc.assignment_id, affected)  # raise → ROLLBACK
            revert_approval_if_approved(self._conn, kc.assignment_id)
        return {"deleted": dto.kc_id}
