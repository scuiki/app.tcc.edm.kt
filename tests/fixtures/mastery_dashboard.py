"""mastery_dashboard montado com a infraestrutura real, sobre o trained_artifact."""

from __future__ import annotations

import pandas as pd
import pytest

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.classroom_import.infrastructure.parquet_cleaned_submissions_store import (
    ParquetCleanedSubmissionsStore,
)
from api.knowledge_components.infrastructure.sqlite_qmatrix_repository import (
    SqliteQMatrixRepository,
)
from api.mastery_dashboard.application.published_model_mastery import PublishedModelMastery
from api.mastery_dashboard.infrastructure.sqlite_student_mastery_repository import (
    SqliteStudentMasteryRepository,
)
from api.model_training.domain.training_dataset import load_training_dataset
from api.model_training.infrastructure.ml_student_mastery_predictor import (
    MlStudentMasteryPredictor,
)
from api.model_training.infrastructure.sqlite_trained_model_repository import (
    SqliteTrainedModelRepository,
)
from api.model_training.infrastructure.trained_model_file_store import TrainedModelFileStore
from api.shared.infrastructure.implementations.sqlite_unit_of_work import SqliteUnitOfWork


def _write_cleaned_submissions(data_root, with_compile_errors: bool) -> None:
    # O Parquet limpo no caminho que o trained_artifact usa ("Turma 6" → turma-6, A439 → 439).
    # Os problemas 1/2/3 batem com a Q-matrix da fixture (o problema 3 liga os dois KCs).
    from api.classroom_import.domain.submission_cleaning import CLEANED_COLUMNS

    base = pd.Timestamp("2019-03-01T08:00:00Z")
    java_a = "public int f(int x) { return x + 1; }"
    java_b = "public int g(int a, int b) { int s = a + b; return s; }"
    java_c = "public boolean h(int n) { if (n > 0) { return true; } return false; }"

    def _row(subject, problem, step, score, code, snapshot_id):
        return {
            "student_id": subject,
            "progsnap_assignment_id": 439,
            "problem_id": problem,
            "code_snapshot_id": snapshot_id,
            "code": code,
            "score": score,
            "submitted_at": base + pd.Timedelta(minutes=step),
            "event_type": "Run.Program",
            "is_correct": int(score == 1.0),
        }

    rows = []
    for si, subj in enumerate(("Sa", "Sb", "Sc")):
        plan = [(1, 0.0, java_a, "x1"), (2, 1.0, java_b, "x2"),
                (1, 1.0, java_a, "x3"), (3, 0.0, java_c, "x4")]
        for step, (pid, score, code, snapshot_id) in enumerate(plan):
            rows.append(_row(subj, pid, si * 10 + step, score, code, f"c{si}_{step}"))
        if with_compile_errors:
            # Como a importação grava de fato: Compile.Error com Java quebrado convive com os
            # Run.Program no MESMO Parquet.
            broken = _row(subj, 1, si * 10 + 5, 0.0, "public int oops( { return ;;; }", "")
            broken["code_snapshot_id"] = f"e{si}"
            broken["event_type"] = "Compile.Error"
            broken["is_correct"] = 0
            rows.append(broken)
    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")

    clean_dir = data_root / "turma-6" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    df[CLEANED_COLUMNS].to_parquet(
        clean_dir / "assignment_439.parquet", engine="pyarrow", index=False
    )


@pytest.fixture
def seed_cleaned_submissions(data_root):
    """Grava o Parquet limpo do assignment do trained_artifact; `with_compile_errors` mistura
    Compile.Error como a importação faz."""

    def seed(with_compile_errors: bool = False) -> None:
        _write_cleaned_submissions(data_root, with_compile_errors)

    return seed


@pytest.fixture
def real_mastery_predictor(trained_artifact) -> MlStudentMasteryPredictor:
    return MlStudentMasteryPredictor(TrainedModelFileStore(trained_artifact.conn))


@pytest.fixture
def sqlite_student_masteries(trained_artifact) -> SqliteStudentMasteryRepository:
    return SqliteStudentMasteryRepository(trained_artifact.conn)


@pytest.fixture
def published_model_mastery(trained_artifact, real_mastery_predictor, sqlite_student_masteries):
    """PublishedModelMastery real; `predictor=` e `student_masteries=` trocam as peças."""
    conn = trained_artifact.conn

    def build(predictor=None, student_masteries=None) -> PublishedModelMastery:
        return PublishedModelMastery(
            assignments=SqliteAssignmentRepository(conn),
            classrooms=SqliteClassroomRepository(conn),
            cleaned_submissions=ParquetCleanedSubmissionsStore(),
            trained_models=SqliteTrainedModelRepository(conn),
            qmatrix=SqliteQMatrixRepository(conn),
            student_masteries=student_masteries or sqlite_student_masteries,
            predictor=predictor or real_mastery_predictor,
            unit_of_work=SqliteUnitOfWork(conn),
        )

    return build


@pytest.fixture
def published_assignment(trained_artifact):
    """O assignment do trained_artifact, relido do banco (com a versão publicada)."""
    return SqliteAssignmentRepository(trained_artifact.conn).get(trained_artifact.assignment_id)


@pytest.fixture
def training_dataset_of(trained_artifact):
    """load_training_dataset(assignment_id) com os repositórios e o Parquet reais."""
    conn = trained_artifact.conn

    def load(assignment_id: int):
        return load_training_dataset(
            assignment_id,
            SqliteAssignmentRepository(conn),
            SqliteClassroomRepository(conn),
            ParquetCleanedSubmissionsStore(),
        )

    return load
