"""Lista os assignments com os DOIS ids — do banco e do ProgSnap2 (backlog 999.2)."""

from __future__ import annotations

import sqlite3

from edmkt_app.persistence import repositories as repos
from edmkt_app.values import ProgSnapAssignmentId


class ListAssignmentsUseCase:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self) -> dict:
        items = []
        for asg in repos.AssignmentRepository(self._conn).list_all():
            try:
                progsnap_id = ProgSnapAssignmentId.from_name(asg.name).value
            except ValueError:
                # Nome sem sufixo numérico: o id ProgSnap2 fica indisponível, a lista não quebra.
                progsnap_id = None
            items.append(
                {
                    "id": asg.id,
                    "progsnap_id": progsnap_id,
                    "name": asg.name,
                    "status": asg.status,
                    "current_version_id": asg.current_version_id,
                }
            )
        return {"assignments": items}
