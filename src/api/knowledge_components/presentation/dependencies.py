# Composition root de knowledge_components, qual implementação cada use case recebe.
from __future__ import annotations

import sqlite3

from fastapi import Depends

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.classrooms.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.assignments.problems.infrastructure.repositories.sqlite_problem_repository import (
    SqliteProblemRepository,
)
from api.classroom_import.infrastructure.repositories.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)
from api.knowledge_components.application.use_cases.add_knowledge_component_use_case import (
    AddKnowledgeComponentUseCase,
)
from api.knowledge_components.application.use_cases.approve_knowledge_components_use_case import (
    ApproveKnowledgeComponentsUseCase,
)
from api.knowledge_components.application.use_cases.get_kc_generation_job_use_case import (
    GetKnowledgeComponentGenerationJobUseCase,
)
from api.knowledge_components.application.use_cases.merge_knowledge_components_use_case import (
    MergeKnowledgeComponentsUseCase,
)
from api.knowledge_components.application.use_cases.remove_knowledge_component_use_case import (
    RemoveKnowledgeComponentUseCase,
)
from api.knowledge_components.application.use_cases.rename_knowledge_component_use_case import (
    RenameKnowledgeComponentUseCase,
)
from api.knowledge_components.application.use_cases.run_kc_generation_use_case import (
    RunKnowledgeComponentGenerationUseCase,
)
from api.knowledge_components.application.use_cases.start_kc_generation_use_case import (
    StartKnowledgeComponentGenerationUseCase,
)
from api.knowledge_components.application.use_cases.list_knowledge_components_use_case import (
    ListKnowledgeComponentsUseCase,
)
from api.knowledge_components.infrastructure.implementations.claude_cli_llm_client import (
    ClaudeCliLLMClient,
)
from api.knowledge_components.infrastructure.implementations.kcgen_kt_generator import (
    KcGenKtGenerator,
)
from api.knowledge_components.infrastructure.implementations.kc_generation_model import (
    KC_GENERATION_MODEL_ID,
)
from api.knowledge_components.infrastructure.repositories.sqlite_kc_generation_job_repository import (
    SqliteKnowledgeComponentGenerationJobRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_problem_knowledge_component_repository import (
    SqliteProblemKnowledgeComponentRepository,
)
from api.shared.infrastructure.implementations.background_jobs import SubprocessJobLauncher
from api.shared.infrastructure.implementations.sqlite_unit_of_work import SqliteUnitOfWork
from api.shared.infrastructure.implementations.one_job_at_a_time_lock import OneJobAtATimeLock
from api.shared.presentation.http.database_session import open_database_session

KC_GENERATION_WORKER = "api.knowledge_components.presentation.workers.kc_generation_worker"


def list_knowledge_components_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> ListKnowledgeComponentsUseCase:
    return ListKnowledgeComponentsUseCase(
        SqliteAssignmentRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteProblemKnowledgeComponentRepository(conn),
    )


def start_kc_generation_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> StartKnowledgeComponentGenerationUseCase:
    return StartKnowledgeComponentGenerationUseCase(
        assignments=SqliteAssignmentRepository(conn),
        jobs=SqliteKnowledgeComponentGenerationJobRepository(conn),
        job_lock=OneJobAtATimeLock(conn),
        launcher=SubprocessJobLauncher(KC_GENERATION_WORKER),
    )


def get_kc_generation_job_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetKnowledgeComponentGenerationJobUseCase:
    return GetKnowledgeComponentGenerationJobUseCase(
        SqliteKnowledgeComponentGenerationJobRepository(conn)
    )


def add_knowledge_component_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> AddKnowledgeComponentUseCase:
    return AddKnowledgeComponentUseCase(
        SqliteAssignmentRepository(conn),
        SqliteProblemRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteProblemKnowledgeComponentRepository(conn),
        SqliteUnitOfWork(conn),
    )


def rename_knowledge_component_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> RenameKnowledgeComponentUseCase:
    return RenameKnowledgeComponentUseCase(
        SqliteAssignmentRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteUnitOfWork(conn),
    )


def remove_knowledge_component_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> RemoveKnowledgeComponentUseCase:
    return RemoveKnowledgeComponentUseCase(
        SqliteAssignmentRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteProblemKnowledgeComponentRepository(conn),
        SqliteUnitOfWork(conn),
    )


def merge_knowledge_components_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> MergeKnowledgeComponentsUseCase:
    return MergeKnowledgeComponentsUseCase(
        SqliteAssignmentRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteProblemKnowledgeComponentRepository(conn),
        SqliteUnitOfWork(conn),
    )


def approve_knowledge_components_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> ApproveKnowledgeComponentsUseCase:
    return ApproveKnowledgeComponentsUseCase(
        SqliteAssignmentRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteUnitOfWork(conn),
    )


def build_run_kc_generation_use_case(
    conn: sqlite3.Connection, llm=None
) -> RunKnowledgeComponentGenerationUseCase:
    # `llm` troca o cliente real do `claude`, os testes passam um falso.
    return RunKnowledgeComponentGenerationUseCase(
        assignments=SqliteAssignmentRepository(conn),
        classrooms=SqliteClassroomRepository(conn),
        problems=SqliteProblemRepository(conn),
        submissions=SqliteSubmissionRepository(conn),
        generator=KcGenKtGenerator(llm or ClaudeCliLLMClient(model=KC_GENERATION_MODEL_ID)),
        knowledge_components=SqliteKnowledgeComponentRepository(conn),
        problem_kcs=SqliteProblemKnowledgeComponentRepository(conn),
        jobs=SqliteKnowledgeComponentGenerationJobRepository(conn),
        unit_of_work=SqliteUnitOfWork(conn),
    )
