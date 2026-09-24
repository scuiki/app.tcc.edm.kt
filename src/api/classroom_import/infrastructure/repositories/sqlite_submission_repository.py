"""ISubmissionRepository sobre SQLite: o dado limpo na tabela `submission`.

Quem lê recebe o mesmo DataFrame que a limpeza produziu, com as mesmas colunas, os mesmos tipos e a
mesma ordem. O treino ordena por `submitted_at` e o ml/ compara ids, então um tipo que mudasse no
caminho (um id que voltasse como texto, um horário sem fuso) mudaria a numérica sem nenhum erro.
"""

from __future__ import annotations

import sqlite3

import pandas as pd

from api.classroom_import.domain.services.submission_cleaning import CLEANED_COLUMNS

# As colunas gravadas, na ordem do INSERT. O progsnap_assignment_id não é gravado por linha: ele
# vem do assignment, pelo JOIN da leitura.
_STORED_COLUMNS = [c for c in CLEANED_COLUMNS if c != "progsnap_assignment_id"]


def _sql_value(value):
    """O valor do pandas no tipo que o sqlite3 aceita: NaN/NA viram NULL, horário vira ISO 8601."""
    if value is None or value is pd.NA or (isinstance(value, float) and value != value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


class SqliteSubmissionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add_many(self, assignment_id: int, events: pd.DataFrame) -> None:
        # .tolist() devolve os tipos do Python (int, float, Timestamp), que o sqlite3 sabe gravar;
        # um numpy.int64 seria recusado.
        columns = [events[c].tolist() for c in _STORED_COLUMNS]
        rows = [(assignment_id, *(_sql_value(v) for v in values)) for values in zip(*columns)]
        placeholders = ", ".join("?" * (len(_STORED_COLUMNS) + 1))
        self._conn.executemany(
            f"INSERT INTO submission (assignment_id, {', '.join(_STORED_COLUMNS)}) "
            f"VALUES ({placeholders});",
            rows,
        )

    def list_by_assignment(self, assignment_id: int) -> pd.DataFrame:
        rows = self._conn.execute(
            "SELECT s.student_id, a.progsnap_assignment_id, s.problem_id, s.code_snapshot_id, "
            "s.code, s.score, s.submitted_at, s.event_type, s.is_correct "
            "FROM submission s JOIN assignment a ON a.id = s.assignment_id "
            "WHERE s.assignment_id = ? ORDER BY s.id;",
            (assignment_id,),
        ).fetchall()
        df = pd.DataFrame([tuple(r) for r in rows], columns=CLEANED_COLUMNS)
        # Os tipos que a limpeza produz. student_id e code_snapshot_id ficam como o SQLite os
        # devolveu: número se o CSV trouxe número, texto se trouxe texto.
        return df.astype(
            {
                "progsnap_assignment_id": "Int64",
                "problem_id": "Int64",
                "score": "float64",
                "is_correct": "int64",
            }
        ).assign(submitted_at=pd.to_datetime(df["submitted_at"], utc=True))
