"""Funde dois KCs: os bindings de kc_drop passam para kc_keep e kc_drop some (KC-02)."""

from __future__ import annotations

from pydantic import BaseModel

from edmkt_app import specs
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence import transaction
from edmkt_app.use_cases.base import BaseWriteUseCase, NotFound
from edmkt_app.use_cases.kc_rules import assert_no_empty_problem, revert_approval_if_approved


class MergeKCDto(BaseModel):
    assignment_id: int
    kc_keep: int
    kc_drop: int


class MergeKCUseCase(BaseWriteUseCase):
    specs = [specs.KCsAreDistinct(), specs.KCsBelongToAssignment()]

    def execute(self, dto: MergeKCDto) -> dict:
        kc_repo = repos.KCRepository(self._conn)
        # Ordem herdada do router: o auto-merge é recusado ANTES do 404, então kc_keep==kc_drop
        # inexistente devolve 409 e não 404. Preservado porque status code é contrato.
        if dto.kc_keep != dto.kc_drop and (
            kc_repo.get(dto.kc_keep) is None or kc_repo.get(dto.kc_drop) is None
        ):
            raise NotFound("KC inexistente")
        return super().execute(dto)

    def _run(self, dto: MergeKCDto) -> dict:
        qmatrix_repo = repos.QMatrixRepository(self._conn)
        # merge = união de bindings; só os problemas de kc_drop poderiam zerar.
        affected = qmatrix_repo.problems_of_kc(dto.kc_drop)
        with transaction(self._conn):
            qmatrix_repo.repoint_bindings(dto.assignment_id, dto.kc_keep, dto.kc_drop)
            repos.KCRepository(self._conn).delete(dto.kc_drop)
            assert_no_empty_problem(self._conn, dto.assignment_id, affected)  # raise → ROLLBACK
            revert_approval_if_approved(self._conn, dto.assignment_id)
        return {"kc_keep": dto.kc_keep, "kc_drop": dto.kc_drop}
