# A matriz aluno × problema que o predictor devolve e o dashboard lê; o conceito é derivado dela.

from __future__ import annotations

StudentMasteryMatrix = dict[tuple[str, int], float]  # `{(student_id, problem_id): mastery}`
