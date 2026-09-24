"""Composition root de mastery_dashboard: qual implementação cada use case recebe.

É aqui que o dashboard recebe o preditor de model_training (a infraestrutura de outra
funcionalidade só entra pela presentation, ligada a uma interface do domínio dela).
"""

from __future__ import annotations

import sqlite3

from fastapi import Depends

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.classroom_import.infrastructure.parquet_cleaned_submissions_store import (
    ParquetCleanedSubmissionsStore,
)
from api.knowledge_components.infrastructure.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.sqlite_qmatrix_repository import (
    SqliteQMatrixRepository,
)
from api.mastery_dashboard.application.get_mastery_use_case import GetMasteryUseCase
from api.mastery_dashboard.application.get_pre_training_statistics_use_case import (
    GetPreTrainingStatisticsUseCase,
)
from api.mastery_dashboard.application.get_recommendations_use_case import (
    GetRecommendationsUseCase,
)
from api.mastery_dashboard.application.published_model_mastery import PublishedModelMastery
from api.mastery_dashboard.infrastructure.sqlite_student_mastery_repository import (
    SqliteStudentMasteryRepository,
)
from api.model_training.infrastructure.ml_student_mastery_predictor import (
    MlStudentMasteryPredictor,
)
from api.model_training.infrastructure.sqlite_trained_model_repository import (
    SqliteTrainedModelRepository,
)
from api.model_training.infrastructure.trained_model_file_store import TrainedModelFileStore
from api.shared.infrastructure.implementations.sqlite_unit_of_work import SqliteUnitOfWork
from api.shared.presentation.http.database_session import open_database_session


def build_published_model_mastery(conn: sqlite3.Connection, predictor=None) -> PublishedModelMastery:
    """`predictor` troca o preditor real (os testes o espionam)."""
    return PublishedModelMastery(
        assignments=SqliteAssignmentRepository(conn),
        classrooms=SqliteClassroomRepository(conn),
        cleaned_submissions=ParquetCleanedSubmissionsStore(),
        trained_models=SqliteTrainedModelRepository(conn),
        qmatrix=SqliteQMatrixRepository(conn),
        student_masteries=SqliteStudentMasteryRepository(conn),
        predictor=predictor or MlStudentMasteryPredictor(TrainedModelFileStore(conn)),
        unit_of_work=SqliteUnitOfWork(conn),
    )


def get_mastery_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetMasteryUseCase:
    return GetMasteryUseCase(SqliteAssignmentRepository(conn), build_published_model_mastery(conn))


def get_recommendations_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetRecommendationsUseCase:
    return GetRecommendationsUseCase(
        SqliteAssignmentRepository(conn),
        SqliteKnowledgeComponentRepository(conn),
        build_published_model_mastery(conn),
    )


def get_pre_training_statistics_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetPreTrainingStatisticsUseCase:
    return GetPreTrainingStatisticsUseCase(
        SqliteAssignmentRepository(conn),
        SqliteClassroomRepository(conn),
        ParquetCleanedSubmissionsStore(),
    )
