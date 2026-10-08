# O dado limpo da importação, as tentativas de cada assignment, com o código Java.

from __future__ import annotations

from typing import Protocol

import pandas as pd


class ISubmissionRepository(Protocol):
    def add_many(self, assignment_id: int, events: pd.DataFrame) -> None:
        # Grava as tentativas de um assignment. `events` tem as colunas de CLEANED_COLUMNS.
        ...

    def count_students(self, assignment_ids: list[int]) -> int:
        # Os alunos distintos com alguma tentativa nesses assignments
        ...

    def list_by_assignment(self, assignment_id: int) -> pd.DataFrame:
        # As tentativas do assignment na ordem gravada, ou um DataFrame vazio se não houver.
        ...

    def list_correct_runs(self, assignment_id: int) -> pd.DataFrame:
        # As execuções corretas, com `submission_id`, `student_id`, `problem_id`, o código e a hora.
        ...

    def count_correct_runs_by_problem(self, assignment_id: int) -> dict[int, int]:
        # Quantas execuções corretas cada problema tem, e o problema sem acerto não volta
        ...
