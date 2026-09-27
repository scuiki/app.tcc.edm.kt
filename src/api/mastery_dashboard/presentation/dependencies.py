# Composition root de mastery_dashboard, qual implementação concreta cada use case recebe.

from __future__ import annotations

import sqlite3

from fastapi import Depends

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.classroom_import.infrastructure.repositories.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_problem_knowledge_component_repository import (
    SqliteProblemKnowledgeComponentRepository,
)
from api.mastery_dashboard.application.use_cases.get_mastery_use_case import GetMasteryUseCase
from api.mastery_dashboard.application.use_cases.get_student_use_case import GetStudentUseCase
from api.mastery_dashboard.application.use_cases.get_submission_statistics_use_case import (
    GetSubmissionStatisticsUseCase,
)
from api.mastery_dashboard.application.use_cases.list_students_use_case import ListStudentsUseCase
from api.mastery_dashboard.application.services.published_model_mastery import PublishedModelMastery
from api.mastery_dashboard.infrastructure.repositories.sqlite_student_mastery_repository import (
    SqliteStudentMasteryRepository,
)
from api.model_training.infrastructure.implementations.ml_student_mastery_predictor import (
    MlStudentMasteryPredictor,
)
from api.model_training.infrastructure.repositories.sqlite_trained_model_repository import (
    SqliteTrainedModelRepository,
)
from api.model_training.infrastructure.implementations.trained_model_file_store import (
    TrainedModelFileStore,
)
from api.shared.infrastructure.implementations.sqlite_unit_of_work import SqliteUnitOfWork
from api.shared.presentation.http.database_session import open_database_session


def build_published_model_mastery(conn: sqlite3.Connection, predictor=None) -> PublishedModelMastery:
    # `predictor` troca o preditor real, os testes o espionam.
    return PublishedModelMastery(
        assignments=SqliteAssignmentRepository(conn),
        submissions=SqliteSubmissionRepository(conn),
        trained_models=SqliteTrainedModelRepository(conn),
        student_masteries=SqliteStudentMasteryRepository(conn),
        predictor=predictor or MlStudentMasteryPredictor(TrainedModelFileStore(conn)),
        unit_of_work=SqliteUnitOfWork(conn),
    )


def get_submission_statistics_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetSubmissionStatisticsUseCase:
    return GetSubmissionStatisticsUseCase(
        SqliteAssignmentRepository(conn),
        SqliteSubmissionRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteProblemKnowledgeComponentRepository(conn),
    )


def get_mastery_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetMasteryUseCase:
    return GetMasteryUseCase(
        SqliteAssignmentRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteProblemKnowledgeComponentRepository(conn),
        build_published_model_mastery(conn),
    )


def list_students_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> ListStudentsUseCase:
    return ListStudentsUseCase(
        SqliteAssignmentRepository(conn),
        SqliteSubmissionRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteProblemKnowledgeComponentRepository(conn),
        build_published_model_mastery(conn),
    )


def get_student_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetStudentUseCase:
    return GetStudentUseCase(
        SqliteAssignmentRepository(conn),
        SqliteSubmissionRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        SqliteProblemKnowledgeComponentRepository(conn),
        build_published_model_mastery(conn),
    )
