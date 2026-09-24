"""Agregados exploratórios da turma — rodam SEM modelo treinado (DASH-04/D-06)."""

from __future__ import annotations

import sqlite3

from api.shared.infrastructure import data_layout
from edmkt_app import eda as eda_module
from edmkt_app.persistence import repositories as repos
from api.shared.domain.errors import NotFound
from edmkt_app.use_cases.base import require_assignment
from api.assignments.domain.progsnap_assignment_id import ProgSnapAssignmentId
from api.assignments.domain.classroom_slug import ClassroomSlug
from api.assignments.infrastructure.sqlite_classroom_repository import SqliteClassroomRepository


class GetEdaUseCase:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, assignment_id: int) -> dict:
        assignment = require_assignment(self._conn, assignment_id)
        turma = SqliteClassroomRepository(self._conn).get(assignment.classroom_id)
        if turma is None:  # WR-01: turma órfã → 404 explícito, não AttributeError em turma.name
            raise NotFound("turma inexistente")

        pq = data_layout.cleaned_submissions_path(
            ClassroomSlug.from_name(turma.name), ProgSnapAssignmentId(assignment.progsnap_assignment_id)
        )
        if not pq.exists():
            # Degrada para agregados vazios quando a ingestão ainda não produziu o Parquet —
            # resiliente sem DADO, não só sem modelo.
            return {
                "assignment_id": assignment_id,
                "success_rate": {},
                "learning_curve": {},
                "compile_error_rate": {},
            }
        return {
            "assignment_id": assignment_id,
            "success_rate": eda_module.success_rate_by_assignment(pq),
            "learning_curve": eda_module.learning_curve(pq),
            "compile_error_rate": eda_module.compile_error_rate_by_assignment(pq),
        }
