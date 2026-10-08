# O DataFrame volta igual ao que foi gravado, tipos inclusive; daí o assert_frame_equal estrito.

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from api.classroom_import.domain.services.submission_cleaning import CLEANED_COLUMNS
from api.classroom_import.infrastructure.repositories.sqlite_submission_repository import (
    CORRECT_RUN_COLUMNS,
    SqliteSubmissionRepository,
)
from tests.fixtures.assignments import add_assignment
from tests.fixtures.classrooms import add_classroom
from tests.fixtures.problems import add_problems
from tests.fixtures.sample_data import cleaned_row, with_cleaned_dtypes


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


def _runs(plan) -> pd.DataFrame:
    # Uma execução por (problema, evento, nota), com o acerto pela regra da limpeza
    return with_cleaned_dtypes(
        pd.DataFrame(
            [
                cleaned_row(f"S{i}", problem, "2019-03-01T08:00:00Z", event, score, "", f"c{i}")
                for i, (problem, event, score) in enumerate(plan)
            ]
        )
    )


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
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db), progsnap_assignment_id=439)
    cleaned = _cleaned(student_ids, snapshot_ids)
    add_problems(tmp_db, assignment_id, [1, 2])

    repo.add_many(assignment_id, cleaned)

    pd.testing.assert_frame_equal(repo.list_by_assignment(assignment_id), cleaned, check_dtype=True)


def test_each_assignment_reads_only_its_own_rows_in_insertion_order(tmp_db):
    repo = SqliteSubmissionRepository(tmp_db)
    classroom_id = add_classroom(tmp_db)
    first = add_assignment(tmp_db, classroom_id, progsnap_assignment_id=439)
    second = add_assignment(tmp_db, classroom_id, progsnap_assignment_id=487)
    add_problems(tmp_db, first, [1, 2])
    add_problems(tmp_db, second, [1])
    repo.add_many(first, _cleaned([3, 1, 2], [30, 10, 20]))
    repo.add_many(second, _cleaned([7], [70]))

    assert repo.list_by_assignment(first)["student_id"].tolist() == [3, 1, 2]  # sem reordenar
    assert repo.list_by_assignment(second)["progsnap_assignment_id"].tolist() == [487]


def test_an_assignment_without_submissions_reads_as_empty_with_the_same_columns(tmp_db):
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))

    empty = SqliteSubmissionRepository(tmp_db).list_by_assignment(assignment_id)

    assert empty.empty
    assert list(empty.columns) == CLEANED_COLUMNS


def test_submissions_for_a_missing_assignment_are_refused(tmp_db):
    with pytest.raises(sqlite3.IntegrityError):
        SqliteSubmissionRepository(tmp_db).add_many(999_999, _cleaned([1], [1]))


def test_the_correct_runs_come_with_their_submission_id(tmp_db):
    repo = SqliteSubmissionRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    add_problems(tmp_db, assignment_id, [1, 2])
    repo.add_many(assignment_id, _cleaned(["S1", "S1", "S2"], ["c1", "c2", "c3"]))

    runs = repo.list_correct_runs(assignment_id)

    correct_ids = [
        row[0] for row in tmp_db.execute("SELECT id FROM submission WHERE is_correct = 1;")
    ]
    assert list(runs.columns) == CORRECT_RUN_COLUMNS
    assert runs["submission_id"].tolist() == correct_ids
    assert runs["code_snapshot_id"].tolist() == ["c3"]  # só a execução correta


@pytest.mark.parametrize(
    ("student_ids", "snapshot_ids"),
    [
        ([9300, 9300, 17], [1720630, 1720631, 5]),
        (["S1", "S1", "S2"], ["c1", "c2", "c3"]),
    ],
    ids=["ids_numericos", "ids_em_texto"],
)
def test_the_correct_runs_keep_the_types_of_the_cleaned_data(tmp_db, student_ids, snapshot_ids):
    repo = SqliteSubmissionRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    cleaned = _cleaned(student_ids, snapshot_ids)
    add_problems(tmp_db, assignment_id, [1, 2])
    repo.add_many(assignment_id, cleaned)

    runs = repo.list_correct_runs(assignment_id)

    columns = CORRECT_RUN_COLUMNS[1:]
    expected = cleaned[cleaned["is_correct"] == 1][columns].reset_index(drop=True)
    pd.testing.assert_frame_equal(runs[columns], expected, check_dtype=True)
    assert runs["submission_id"].dtype == "int64"


def test_each_assignment_reads_only_its_own_correct_runs(tmp_db):
    # O mesmo problema existe nos dois exercícios, e só o filtro do exercício separa as execuções
    repo = SqliteSubmissionRepository(tmp_db)
    classroom_id = add_classroom(tmp_db)
    first = add_assignment(tmp_db, classroom_id, progsnap_assignment_id=439)
    second = add_assignment(tmp_db, classroom_id, progsnap_assignment_id=487)
    add_problems(tmp_db, first, [1, 2])
    add_problems(tmp_db, second, [1, 2])
    repo.add_many(first, _cleaned(["S1", "S1", "S2"], ["c1", "c2", "c3"]))
    repo.add_many(second, _cleaned(["S7", "S7", "S8"], ["c7", "c8", "c9"]))

    assert repo.list_correct_runs(first)["code_snapshot_id"].tolist() == ["c3"]
    assert repo.list_correct_runs(second)["code_snapshot_id"].tolist() == ["c9"]


def test_an_assignment_without_a_correct_run_reads_as_empty_with_the_same_columns(tmp_db):
    repo = SqliteSubmissionRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    add_problems(tmp_db, assignment_id, [1, 2])
    repo.add_many(assignment_id, _cleaned(["S1", "S1"], ["c1", "c2"]))  # nenhuma correta

    runs = repo.list_correct_runs(assignment_id)

    assert runs.empty
    assert list(runs.columns) == CORRECT_RUN_COLUMNS


def test_only_the_correct_runs_are_counted_by_problem(tmp_db):
    # A nota 1.0 no Compile.Error mostra que o filtro é o acerto, e não a nota
    repo = SqliteSubmissionRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    add_problems(tmp_db, assignment_id, [1, 2, 3])
    repo.add_many(
        assignment_id,
        _runs(
            [
                (1, "Run.Program", 1.0),
                (1, "Run.Program", 0.5),
                (1, "Run.Program", 1.0),
                (2, "Run.Program", 1.0),
                (2, "Compile.Error", 1.0),
                (3, "Run.Program", 0.0),
                (3, "Compile.Error", float("nan")),
            ]
        ),
    )

    # O problema 3 não tem acerto e não volta
    assert repo.count_correct_runs_by_problem(assignment_id) == {1: 2, 2: 1}


def test_a_correct_run_without_a_problem_is_not_counted(tmp_db):
    repo = SqliteSubmissionRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    add_problems(tmp_db, assignment_id, [1])
    repo.add_many(assignment_id, _runs([(1, "Run.Program", 1.0), (None, "Run.Program", 1.0)]))

    assert repo.count_correct_runs_by_problem(assignment_id) == {1: 1}


def test_each_assignment_counts_only_its_own_correct_runs(tmp_db):
    # O mesmo problema existe nos dois exercícios, e só o filtro do exercício separa as execuções
    repo = SqliteSubmissionRepository(tmp_db)
    classroom_id = add_classroom(tmp_db)
    first = add_assignment(tmp_db, classroom_id, progsnap_assignment_id=439)
    second = add_assignment(tmp_db, classroom_id, progsnap_assignment_id=487)
    add_problems(tmp_db, first, [1])
    add_problems(tmp_db, second, [1, 2])
    repo.add_many(first, _runs([(1, "Run.Program", 1.0)]))
    repo.add_many(second, _runs([(1, "Run.Program", 1.0)] * 3 + [(2, "Run.Program", 1.0)]))

    assert repo.count_correct_runs_by_problem(first) == {1: 1}
    assert repo.count_correct_runs_by_problem(second) == {1: 3, 2: 1}


def test_an_assignment_without_a_correct_run_counts_nothing(tmp_db):
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))

    assert SqliteSubmissionRepository(tmp_db).count_correct_runs_by_problem(assignment_id) == {}


def test_the_codes_come_back_by_submission_id_with_line_breaks_and_tabs_intact(tmp_db):
    repo = SqliteSubmissionRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    add_problems(tmp_db, assignment_id, [1])
    codes = ["int f() {\r\n\treturn 1;\r\n}", "int g() {\n\treturn 2;\n}\n"]
    rows = [
        cleaned_row(f"S{i}", 1, "2019-03-01T08:00:00Z", "Run.Program", 1.0, code, f"c{i}")
        for i, code in enumerate(codes)
    ]
    repo.add_many(assignment_id, with_cleaned_dtypes(pd.DataFrame(rows)))
    first, second = [row[0] for row in tmp_db.execute("SELECT id FROM submission ORDER BY id;")]

    # O id que não existe some da resposta, sem erro
    assert repo.get_codes([second, 999_999, first]) == {first: codes[0], second: codes[1]}


def test_no_submission_id_gives_no_code(tmp_db):
    assert SqliteSubmissionRepository(tmp_db).get_codes([]) == {}
