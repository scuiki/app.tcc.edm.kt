"""QMatrixBinding: uma linha da Q-matrix, "o problema P exige o KC K"."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QMatrixBinding:
    id: int | None
    assignment_id: int
    kc_id: int
    problem_id: int
