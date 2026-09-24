# Composition root de classrooms; a listagem com as contagens vem de classroom_import.

from __future__ import annotations

import sqlite3

from fastapi import Depends

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.problems.infrastructure.repositories.sqlite_problem_repository import (
    SqliteProblemRepository,
)
from api.classroom_import.application.use_cases.list_classrooms_use_case import (
    ListClassroomsUseCase,
)
from api.classroom_import.infrastructure.repositories.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)
from api.classrooms.application.use_cases.create_classroom_use_case import CreateClassroomUseCase
from api.classrooms.application.use_cases.remove_classroom_use_case import RemoveClassroomUseCase
from api.classrooms.application.use_cases.rename_classroom_use_case import RenameClassroomUseCase
from api.classrooms.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.shared.infrastructure.implementations.sqlite_unit_of_work import SqliteUnitOfWork
from api.shared.presentation.http.database_session import open_database_session


def list_classrooms_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> ListClassroomsUseCase:
    return ListClassroomsUseCase(
        SqliteClassroomRepository(conn),
        SqliteAssignmentRepository(conn),
        SqliteProblemRepository(conn),
        SqliteSubmissionRepository(conn),
    )


def create_classroom_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> CreateClassroomUseCase:
    return CreateClassroomUseCase(SqliteClassroomRepository(conn), SqliteUnitOfWork(conn))


def rename_classroom_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> RenameClassroomUseCase:
    return RenameClassroomUseCase(SqliteClassroomRepository(conn), SqliteUnitOfWork(conn))


def remove_classroom_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> RemoveClassroomUseCase:
    return RemoveClassroomUseCase(
        SqliteClassroomRepository(conn), SqliteAssignmentRepository(conn), SqliteUnitOfWork(conn)
    )
