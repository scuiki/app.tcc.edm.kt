"""O dado limpo da importação: as tentativas de cada assignment, com o código Java."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class ISubmissionRepository(Protocol):
    def add_many(self, assignment_id: int, events: pd.DataFrame) -> None:
        """Grava as tentativas de um assignment. `events` tem as colunas de CLEANED_COLUMNS."""
        ...

    def list_by_assignment(self, assignment_id: int) -> pd.DataFrame:
        """As tentativas do assignment, nas colunas e nos tipos de CLEANED_COLUMNS, na ordem em que
        foram gravadas. Sem tentativas, um DataFrame vazio com as mesmas colunas."""
        ...
