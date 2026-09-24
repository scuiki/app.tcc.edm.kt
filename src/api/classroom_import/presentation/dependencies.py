"""Composition root de classroom_import: qual implementação cada use case recebe."""

from __future__ import annotations

import sqlite3

from fastapi import Depends

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.classroom_import.application.import_classroom_dataset_use_case import (
    ImportClassroomDatasetUseCase,
)
from api.classroom_import.application.upload_classroom_dataset_use_case import (
    UploadClassroomDatasetUseCase,
)
from api.classroom_import.infrastructure.parquet_cleaned_submissions_store import (
    ParquetCleanedSubmissionsStore,
)
from api.classroom_import.infrastructure.progsnap_csv_reader import ProgSnapCsvReader
from api.classroom_import.infrastructure.progsnap_zip_extractor import ProgSnapZipExtractor
from api.classroom_import.infrastructure.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)
from api.shared.infrastructure.implementations.sqlite_unit_of_work import SqliteUnitOfWork
from api.shared.infrastructure.implementations.one_job_at_a_time_lock import OneJobAtATimeLock
from api.shared.presentation.http.database_session import open_database_session


def upload_classroom_dataset_use_case() -> UploadClassroomDatasetUseCase:
    return UploadClassroomDatasetUseCase(ProgSnapZipExtractor())


def import_classroom_dataset_use_case(
    conn: sqlite3.Connection = Depends(open_database_session),
) -> ImportClassroomDatasetUseCase:
    return build_import_classroom_dataset_use_case(conn)


def build_import_classroom_dataset_use_case(conn: sqlite3.Connection) -> ImportClassroomDatasetUseCase:
    return ImportClassroomDatasetUseCase(
        classrooms=SqliteClassroomRepository(conn),
        assignments=SqliteAssignmentRepository(conn),
        submissions=SqliteSubmissionRepository(conn),
        unit_of_work=SqliteUnitOfWork(conn),
        job_lock=OneJobAtATimeLock(conn),
        tables=ProgSnapCsvReader(),
        cleaned_submissions=ParquetCleanedSubmissionsStore(),
    )
