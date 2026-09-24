"""ISubmissionRepository sobre SQLite: o score contínuo, nunca o binário, nunca o código Java."""

from __future__ import annotations

import sqlite3

from api.classroom_import.domain.entities.submission_entity import Submission


class SqliteSubmissionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, submission: Submission) -> int:
        cur = self._conn.execute(
            "INSERT INTO submission "
            "(assignment_id, code_snapshot_id, student_id, problem_id, score, created_at, "
            "event_type) VALUES (?, ?, ?, ?, ?, ?, ?);",
            (
                submission.assignment_id,
                submission.code_snapshot_id,
                submission.student_id,
                submission.problem_id,
                submission.score,
                submission.created_at,
                submission.event_type,
            ),
        )
        return cur.lastrowid
