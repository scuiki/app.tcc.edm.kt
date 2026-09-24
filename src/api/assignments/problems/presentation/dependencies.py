# Composition root de problems; a Q-matrix vem de knowledge_components, montada aqui.

from __future__ import annotations

import sqlite3

from fastapi import Depends

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.problems.application.use_cases.list_problems_use_case import (
    ListProblemsUseCase,
)
from api.assignments.problems.infrastructure.repositories.sqlite_problem_repository import (
    SqliteProblemRepository,
)
from api.knowledge_components.application.use_cases.get_qmatrix_use_case import GetQMatrixUseCase
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_qmatrix_repository import (
    SqliteQMatrixRepository,
)
from api.shared.presentation.http.database_session import open_database_session


def list_problems_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> ListProblemsUseCase:
    return ListProblemsUseCase(SqliteAssignmentRepository(conn), SqliteProblemRepository(conn))


def get_qmatrix_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetQMatrixUseCase:
    return GetQMatrixUseCase(
        SqliteAssignmentRepository(conn),
        SqliteProblemRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteQMatrixRepository(conn),
    )
