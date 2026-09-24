"""Submission: uma tentativa do aluno, como fica no banco.

Guarda o score CONTÍNUO (nunca o binário) e nunca o código Java: o snapshot fica só no Parquet.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Submission:
    id: int | None
    assignment_id: int
    code_snapshot_id: str
    student_id: str | None
    problem_id: int | None
    score: float | None
    created_at: str
    event_type: str | None = None
