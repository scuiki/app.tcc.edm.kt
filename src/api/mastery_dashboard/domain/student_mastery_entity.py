"""StudentMastery: a probabilidade de domínio de um aluno em um KC, segundo uma versão de modelo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StudentMastery:
    id: int | None
    trained_model_id: int  # a mastery vale para a versão que a calculou
    student_id: str
    kc_id: int
    mastery: float | None
