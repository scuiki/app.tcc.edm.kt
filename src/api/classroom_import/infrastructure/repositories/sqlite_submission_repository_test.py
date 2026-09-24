# O DataFrame volta igual ao que foi gravado, tipos inclusive; daí o assert_frame_equal estrito.

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from api.classroom_import.domain.services.submission_cleaning import CLEANED_COLUMNS
from api.classroom_import.infrastructure.repositories.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)
from tests.fixtures.problems import add_problems


def _assignment_id(conn, progsnap_assignment_id: int = 439) -> int:
    classroom_id = conn.execute(
        "INSERT INTO classroom (name, created_at) VALUES ('T', 't0');"
    ).lastrowid
    return conn.execute(
        "INSERT INTO assignment (classroom_id, name, created_at, progsnap_assignment_id) "
        "VALUES (?, 'A', 't0', ?);",
        (classroom_id, progsnap_assignment_id),
    ).lastrowid


def _cleaned(student_ids, snapshot_ids) -> pd.DataFrame:
    # Um dado limpo com os tipos que a limpeza produz.
    n = len(student_ids)
    df = pd.DataFrame(
        {
            "student_id": student_ids,
            "progsnap_assignment_id": pd.array([439] * n, dtype="Int64"),
            "problem_id": pd.array([1, 2, 1][:n], dtype="Int64"),
            "code_snapshot_id": snapshot_ids,
            "code": ["int f(){return 0;}", "int g(){\n  return 1;\n}", ""][:n],
            "score": [0.5, float("nan"), 1.0][:n],  # contínuo, e nulo num Compile.Error
            "submitted_at": pd.to_datetime(
                ["2019-03-01T08:00:00Z", "2019-03-01T08:01:00Z", "2019-03-01T08:02:30Z"][:n],
                utc=True,
            ),
            "event_type": ["Run.Program", "Compile.Error", "Run.Program"][:n],
            "is_correct": [0, 0, 1][:n],
        }
    )
    return df[CLEANED_COLUMNS]


@pytest.mark.parametrize(
    ("student_ids", "snapshot_ids"),
    [
        ([9300, 9300, 17], [1720630, 1720631, 5]),  # CSEDM, o CSV traz números
        (["S1", "S1", "S2"], ["c1", "c2", "c3"]),  # outro dataset, texto
    ],
    ids=["ids_numericos", "ids_em_texto"],
)
def test_the_cleaned_data_comes_back_identical(tmp_db, student_ids, snapshot_ids):
    repo = SqliteSubmissionRepository(tmp_db)
    assignment_id = _assignment_id(tmp_db)
    cleaned = _cleaned(student_ids, snapshot_ids)
    add_problems(tmp_db, assignment_id, [1, 2])

    repo.add_many(assignment_id, cleaned)

    pd.testing.assert_frame_equal(repo.list_by_assignment(assignment_id), cleaned, check_dtype=True)


def test_each_assignment_reads_only_its_own_rows_in_insertion_order(tmp_db):
    repo = SqliteSubmissionRepository(tmp_db)
    first, second = _assignment_id(tmp_db, 439), _assignment_id(tmp_db, 487)
    add_problems(tmp_db, first, [1, 2])
    add_problems(tmp_db, second, [1])
    repo.add_many(first, _cleaned([3, 1, 2], [30, 10, 20]))
    repo.add_many(second, _cleaned([7], [70]))

    assert repo.list_by_assignment(first)["student_id"].tolist() == [3, 1, 2]  # sem reordenar
    assert repo.list_by_assignment(second)["progsnap_assignment_id"].tolist() == [487]


def test_an_assignment_without_submissions_reads_as_empty_with_the_same_columns(tmp_db):
    empty = SqliteSubmissionRepository(tmp_db).list_by_assignment(_assignment_id(tmp_db))

    assert empty.empty
    assert list(empty.columns) == CLEANED_COLUMNS


def test_submissions_for_a_missing_assignment_are_refused(tmp_db):
    with pytest.raises(sqlite3.IntegrityError):
        SqliteSubmissionRepository(tmp_db).add_many(999_999, _cleaned([1], [1]))
