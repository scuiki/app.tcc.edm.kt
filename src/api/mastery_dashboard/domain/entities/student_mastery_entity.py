# StudentMastery, a chance prevista de um aluno acertar um problema agora, por versão de modelo.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StudentMastery:
    id: int | None
    trained_model_id: int  # a mastery vale para a versão que a calculou
    student_id: str
    problem_id: int
    mastery: float | None
