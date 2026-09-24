# O DataFrame lido tem que voltar com as mesmas colunas, tipos e ordem que a limpeza produziu.

from __future__ import annotations

import sqlite3

import pandas as pd

from api.classroom_import.domain.services.submission_cleaning import CLEANED_COLUMNS

# Colunas gravadas na ordem do INSERT; progsnap_assignment_id vem do assignment via JOIN.
_STORED_COLUMNS = [c for c in CLEANED_COLUMNS if c != "progsnap_assignment_id"]


def _sql_value(value):
    # O valor do pandas no tipo que o sqlite3 aceita; NaN/NA viram NULL, horário vira ISO 8601.
    if value is None or value is pd.NA or (isinstance(value, float) and value != value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


class SqliteSubmissionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add_many(self, assignment_id: int, events: pd.DataFrame) -> None:
        # .tolist() devolve tipos do Python que o sqlite3 grava; numpy.int64 seria recusado.
        columns = [events[c].tolist() for c in _STORED_COLUMNS]
        rows = [(assignment_id, *(_sql_value(v) for v in values)) for values in zip(*columns)]
        placeholders = ", ".join("?" * (len(_STORED_COLUMNS) + 1))
        self._conn.executemany(
            f"INSERT INTO submission (assignment_id, {', '.join(_STORED_COLUMNS)}) "
            f"VALUES ({placeholders});",
            rows,
        )

    def count_students(self, assignment_ids: list[int]) -> int:
        if not assignment_ids:
            return 0
        placeholders = ", ".join("?" * len(assignment_ids))
        row = self._conn.execute(
            f"SELECT COUNT(DISTINCT student_id) FROM submission "
            f"WHERE assignment_id IN ({placeholders});",
            assignment_ids,
        ).fetchone()
        return row[0]

    def list_by_assignment(self, assignment_id: int) -> pd.DataFrame:
        rows = self._conn.execute(
            "SELECT s.student_id, a.progsnap_assignment_id, s.problem_id, s.code_snapshot_id, "
            "s.code, s.score, s.submitted_at, s.event_type, s.is_correct "
            "FROM submission s JOIN assignment a ON a.id = s.assignment_id "
            "WHERE s.assignment_id = ? ORDER BY s.id;",
            (assignment_id,),
        ).fetchall()
        df = pd.DataFrame([tuple(r) for r in rows], columns=CLEANED_COLUMNS)
        # Os tipos que a limpeza produz; student_id/code_snapshot_id ficam como o SQLite devolveu.
        return df.astype(
            {
                "progsnap_assignment_id": "Int64",
                "problem_id": "Int64",
                "score": "float64",
                "is_correct": "int64",
            }
        ).assign(submitted_at=pd.to_datetime(df["submitted_at"], utc=True))
