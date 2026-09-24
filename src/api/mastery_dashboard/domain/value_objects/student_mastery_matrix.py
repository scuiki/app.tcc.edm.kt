"""A matriz aluno × KC que o predictor devolve e o dashboard lê."""

from __future__ import annotations

StudentMasteryMatrix = dict[tuple[str, int], float]  # {(student_id, kc_id): mastery}
