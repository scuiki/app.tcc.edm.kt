"""SqliteSubmissionRepository: grava a tentativa fielmente, sem o código, e respeita a FK."""

from __future__ import annotations

import sqlite3

import pytest

from api.classroom_import.domain.submission_entity import Submission
from api.classroom_import.infrastructure.sqlite_submission_repository import (
    SqliteSubmissionRepository,
)


def _assignment_id(conn) -> int:
    classroom_id = conn.execute(
        "INSERT INTO classroom (name, created_at) VALUES ('T', 't0');"
    ).lastrowid
    return conn.execute(
        "INSERT INTO assignment (classroom_id, name, created_at) VALUES (?, 'A', 't0');",
        (classroom_id,),
    ).lastrowid


def _submission(assignment_id: int, **fields) -> Submission:
    values = dict(
        id=None, assignment_id=assignment_id, code_snapshot_id="cs1", student_id="S1",
        problem_id=1, score=0.5, created_at="t0", event_type="Run.Program",
    )
    values.update(fields)
    return Submission(**values)


def test_add_stores_every_field(tmp_db):
    assignment_id = _assignment_id(tmp_db)

    submission_id = SqliteSubmissionRepository(tmp_db).add(_submission(assignment_id))

    row = tmp_db.execute(
        "SELECT assignment_id, code_snapshot_id, student_id, problem_id, score, created_at, "
        "event_type FROM submission WHERE id = ?;",
        (submission_id,),
    ).fetchone()
    # O score contínuo (0.5) fica como veio: o binário é derivado no dado limpo, não aqui.
    assert tuple(row) == (assignment_id, "cs1", "S1", 1, 0.5, "t0", "Run.Program")


def test_a_submission_for_a_missing_assignment_is_refused(tmp_db):
    with pytest.raises(sqlite3.IntegrityError):
        SqliteSubmissionRepository(tmp_db).add(_submission(assignment_id=999_999))
