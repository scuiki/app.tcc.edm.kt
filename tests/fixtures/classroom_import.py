"""classroom_import montado com a infraestrutura real."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.classroom_import.application.import_classroom_dataset_dto import ImportClassroomDatasetDTO
from api.classroom_import.application.import_classroom_dataset_use_case import (
    ImportClassroomDatasetUseCase,
)
from api.classroom_import.infrastructure.parquet_cleaned_submissions_store import (
    ParquetCleanedSubmissionsStore,
)
from api.classroom_import.infrastructure.progsnap_csv_reader import ProgSnapCsvReader
from api.classroom_import.infrastructure.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)
from api.shared.infrastructure.implementations.sqlite_unit_of_work import SqliteUnitOfWork
from api.shared.infrastructure.implementations.one_job_at_a_time_lock import OneJobAtATimeLock


@pytest.fixture
def sqlite_submissions(tmp_db) -> SqliteSubmissionRepository:
    return SqliteSubmissionRepository(tmp_db)


@pytest.fixture
def import_classroom(tmp_db, sqlite_submissions):
    """Importa uma MainTable pelo use case real; `submissions=` troca o repositório (falhas)."""

    def run(raw_dir: Path, classroom_name: str, main_table: Path, *, submissions=None):
        use_case = ImportClassroomDatasetUseCase(
            classrooms=SqliteClassroomRepository(tmp_db),
            assignments=SqliteAssignmentRepository(tmp_db),
            submissions=submissions or sqlite_submissions,
            unit_of_work=SqliteUnitOfWork(tmp_db),
            job_lock=OneJobAtATimeLock(tmp_db),
            tables=ProgSnapCsvReader(),
            cleaned_submissions=ParquetCleanedSubmissionsStore(),
        )
        return use_case.execute(
            ImportClassroomDatasetDTO(
                classroom_name=classroom_name, raw_dir=raw_dir, main_table=main_table
            )
        )

    return run
