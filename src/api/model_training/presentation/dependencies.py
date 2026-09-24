# Composition root de model_training, qual implementação cada use case recebe.

from __future__ import annotations

import sqlite3

from fastapi import Depends

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.classrooms.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.classroom_import.infrastructure.repositories.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)
from api.model_training.application.use_cases.get_training_job_use_case import GetTrainingJobUseCase
from api.model_training.application.use_cases.get_training_loss_history_use_case import (
    GetTrainingLossHistoryUseCase,
)
from api.model_training.application.use_cases.run_training_use_case import RunTrainingUseCase
from api.model_training.application.use_cases.start_training_use_case import StartTrainingUseCase
from api.model_training.infrastructure.implementations.ml_code_dkt_trainer import MlCodeDktTrainer
from api.model_training.infrastructure.repositories.sqlite_training_epoch_metric_repository import (
    SqliteTrainingEpochMetricRepository,
)
from api.model_training.infrastructure.repositories.sqlite_training_job_repository import (
    SqliteTrainingJobRepository,
)
from api.model_training.infrastructure.implementations.trained_model_file_store import (
    TrainedModelFileStore,
)
from api.shared.infrastructure.implementations.background_jobs import SubprocessJobLauncher
from api.shared.infrastructure.implementations.sqlite_unit_of_work import SqliteUnitOfWork
from api.shared.infrastructure.implementations.one_job_at_a_time_lock import OneJobAtATimeLock
from api.shared.presentation.http.database_session import open_database_session

TRAINING_WORKER = "api.model_training.presentation.workers.training_worker"


def start_training_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> StartTrainingUseCase:
    return StartTrainingUseCase(
        assignments=SqliteAssignmentRepository(conn),
        jobs=SqliteTrainingJobRepository(conn),
        job_lock=OneJobAtATimeLock(conn),
        launcher=SubprocessJobLauncher(TRAINING_WORKER),
    )


def get_training_job_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetTrainingJobUseCase:
    return GetTrainingJobUseCase(
        SqliteTrainingJobRepository(conn), SqliteTrainingEpochMetricRepository(conn)
    )


def get_training_loss_history_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> GetTrainingLossHistoryUseCase:
    return GetTrainingLossHistoryUseCase(
        SqliteTrainingJobRepository(conn), SqliteTrainingEpochMetricRepository(conn)
    )


def build_run_training_use_case(
    conn: sqlite3.Connection, trainer: MlCodeDktTrainer | None = None
) -> RunTrainingUseCase:
    # O corpo do worker; `trainer` troca o treinador real (os testes passam um rápido ou falho).
    return RunTrainingUseCase(
        assignments=SqliteAssignmentRepository(conn),
        classrooms=SqliteClassroomRepository(conn),
        submissions=SqliteSubmissionRepository(conn),
        trainer=trainer or MlCodeDktTrainer(),
        model_store=TrainedModelFileStore(conn),
        jobs=SqliteTrainingJobRepository(conn),
        epoch_metrics=SqliteTrainingEpochMetricRepository(conn),
        unit_of_work=SqliteUnitOfWork(conn),
    )
