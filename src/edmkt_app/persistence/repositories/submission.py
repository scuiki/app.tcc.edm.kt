"""Submission: o evento cru persistido (Score CONTÍNUO, nunca o binário, nunca o Code)."""

from __future__ import annotations

import sqlite3

from edmkt_app.persistence import models


class SubmissionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, submission: models.Submission) -> int:
        cur = self._conn.execute(
            "INSERT INTO submission "
            "(assignment_id, code_state_id, subject_id, problem_id, score, created_at, event_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?);",
            (
                submission.assignment_id,
                submission.code_state_id,
                submission.subject_id,
                submission.problem_id,
                submission.score,
                submission.created_at,
                submission.event_type,
            ),
        )
        return cur.lastrowid
