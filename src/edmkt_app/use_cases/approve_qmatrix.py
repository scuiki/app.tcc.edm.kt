"""Fecha o gate humano: a Q-matrix rascunhada pelo LLM vira aprovada pelo professor (KC-03)."""

from __future__ import annotations

from pydantic import BaseModel

from edmkt_app import specs
from api.shared.infrastructure.database.sqlite_connection import transaction
from edmkt_app.use_cases.base import BaseWriteUseCase, require_assignment
from api.assignments.infrastructure.sqlite_assignment_repository import SqliteAssignmentRepository


class ApproveQMatrixDto(BaseModel):
    assignment_id: int


class ApproveQMatrixUseCase(BaseWriteUseCase):
    # É o ÚNICO caminho que destrava o /training (D-06), então as duas regras são duras.
    specs = [specs.AssignmentIsDraft(), specs.AssignmentHasKCs()]

    def execute(self, dto: ApproveQMatrixDto) -> dict:
        # Inexistência é fail-fast (404) e não entra no acúmulo: sem alvo, não há regra a aplicar.
        require_assignment(self._conn, dto.assignment_id)
        return super().execute(dto)

    def _run(self, dto: ApproveQMatrixDto) -> dict:
        with transaction(self._conn):
            SqliteAssignmentRepository(self._conn).set_status(dto.assignment_id, "kc_approved")
        return {"assignment_id": dto.assignment_id, "status": "kc_approved"}
