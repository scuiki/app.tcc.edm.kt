"""Composition root de assignments: qual implementação cada use case recebe."""

from __future__ import annotations

import sqlite3

from fastapi import Depends

from api.assignments.application.use_cases.list_assignments_use_case import ListAssignmentsUseCase
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.shared.presentation.http.database_session import open_database_session


def list_assignments_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> ListAssignmentsUseCase:
    return ListAssignmentsUseCase(SqliteAssignmentRepository(conn))
