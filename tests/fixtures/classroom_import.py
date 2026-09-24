# classroom_import montado com a infraestrutura real, e o dado de upload dos testes.

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.classrooms.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.assignments.problems.infrastructure.repositories.sqlite_problem_repository import (
    SqliteProblemRepository,
)
from api.classroom_import.application.dtos.import_classroom_dataset_dto import (
    ImportClassroomDatasetDTO,
)
from api.classroom_import.application.use_cases.import_classroom_dataset_use_case import (
    ImportClassroomDatasetUseCase,
)
from api.classroom_import.infrastructure.implementations.progsnap_csv_reader import (
    ProgSnapCsvReader,
)
from api.classroom_import.infrastructure.repositories.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)
from api.shared.infrastructure.implementations.sqlite_unit_of_work import SqliteUnitOfWork
from api.shared.infrastructure.implementations.one_job_at_a_time_lock import OneJobAtATimeLock
from tests.fixtures.sample_data import (
    JAVA_OK_A,
    JAVA_OK_B,
    as_progsnap_upload,
    cleaned_row,
    with_cleaned_dtypes,
)


@pytest.fixture
def sqlite_submissions(tmp_db) -> SqliteSubmissionRepository:
    return SqliteSubmissionRepository(tmp_db)


@pytest.fixture
def import_classroom(tmp_db, sqlite_submissions):
    # Importa uma MainTable pelo use case real, e `submissions=` troca o repositório

    def run(raw_dir: Path, classroom_name: str, main_table: Path, *, submissions=None):
        use_case = ImportClassroomDatasetUseCase(
            classrooms=SqliteClassroomRepository(tmp_db),
            assignments=SqliteAssignmentRepository(tmp_db),
            problems=SqliteProblemRepository(tmp_db),
            submissions=submissions or sqlite_submissions,
            unit_of_work=SqliteUnitOfWork(tmp_db),
            job_lock=OneJobAtATimeLock(tmp_db),
            tables=ProgSnapCsvReader(),
        )
        return use_case.execute(
            ImportClassroomDatasetDTO(
                classroom_name=classroom_name, raw_dir=raw_dir, main_table=main_table
            )
        )

    return run


@pytest.fixture
def a439_mini_progsnap(a439_mini) -> pd.DataFrame:
    # O mesmo a439_mini, na forma em que chega no upload do professor
    return as_progsnap_upload(a439_mini)


@pytest.fixture
def ingest_orphan_df() -> tuple[pd.DataFrame, dict[str, str]]:
    # Um evento aponta para um CodeStateID que não existe no CodeStates
    code_states = {"c1": JAVA_OK_A, "c2": JAVA_OK_B}
    rows = [
        cleaned_row("S1", 1, "2019-03-01T08:00:00Z", "Run.Program", 1.0, JAVA_OK_A, "c1"),
        cleaned_row("S1", 2, "2019-03-01T08:01:00Z", "Run.Program", 0.0, JAVA_OK_B, "c2"),
        cleaned_row("S2", 1, "2019-03-01T08:02:00Z", "Run.Program", 1.0, "", "c_orphan"),
    ]
    return as_progsnap_upload(with_cleaned_dtypes(pd.DataFrame(rows))), code_states


@pytest.fixture
def ingest_single_class_df() -> pd.DataFrame:
    # Todos os first-attempts acertam, então o AUC é indefinido e não dá para treinar
    rows = [
        cleaned_row("S1", 1, "2019-03-01T08:00:00Z", "Run.Program", 1.0, JAVA_OK_A, "c1"),
        cleaned_row("S2", 1, "2019-03-01T08:01:00Z", "Run.Program", 1.0, JAVA_OK_A, "c2"),
        cleaned_row("S3", 2, "2019-03-01T08:02:00Z", "Run.Program", 1.0, JAVA_OK_B, "c3"),
    ]
    return with_cleaned_dtypes(pd.DataFrame(rows))


@pytest.fixture
def ingest_bom_csv(tmp_path) -> Path:
    # Um MainTable.csv salvo com BOM, que a leitura precisa aceitar
    main = tmp_path / "MainTable.csv"
    main.write_text(
        "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp\n"
        "S1,439,1,c1,Run.Program,1.0,2019-03-01T08:00:00Z\n",
        encoding="utf-8-sig",
    )
    return main


@pytest.fixture
def ingest_layout_dir(tmp_path) -> Path:
    # O CodeStates em LinkTables/, como no CodeWorkout, e duas MainTable para o professor escolher
    (tmp_path / "LinkTables").mkdir()
    (tmp_path / "LinkTables" / "CodeStates.csv").write_text(
        "CodeStateID,Code\nc1,\"public int f(){return 1;}\"\n", encoding="utf-8"
    )
    for variant in ("All", "Train"):
        (tmp_path / variant).mkdir()
        (tmp_path / variant / "MainTable.csv").write_text(
            "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp\n"
            "S1,439,1,c1,Run.Program,1.0,2019-03-01T08:00:00Z\n",
            encoding="utf-8",
        )
    return tmp_path
