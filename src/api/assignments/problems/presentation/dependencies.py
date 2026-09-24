# Composition root de problems; os KCs de cada problema vêm de knowledge_components, montados aqui.

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
from api.knowledge_components.application.use_cases.list_problem_knowledge_components_use_case import (
    ListProblemKnowledgeComponentsUseCase,
)
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_problem_knowledge_component_repository import (
    SqliteProblemKnowledgeComponentRepository,
)
from api.shared.presentation.http.database_session import open_database_session


def list_problems_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> ListProblemsUseCase:
    return ListProblemsUseCase(SqliteAssignmentRepository(conn), SqliteProblemRepository(conn))


def list_problem_knowledge_components_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> ListProblemKnowledgeComponentsUseCase:
    return ListProblemKnowledgeComponentsUseCase(
        SqliteAssignmentRepository(conn),
        SqliteProblemRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteProblemKnowledgeComponentRepository(conn),
    )
