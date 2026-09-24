# Code-DKT prevê por problema; a Q-matrix agrega isso em mastery por KC (nunca indexar por kc_id).

from __future__ import annotations

import pandas as pd


def aggregate_student_mastery(
    predictions: pd.DataFrame, qmatrix: dict[int, list[int]]
) -> dict[tuple[str, int], float]:
    # Devolve `{(student_id, kc_id): mastery}`; mastery do KC é a média sobre os problemas dele.
    if predictions.empty:
        return {}

    # A última linha vence por (aluno, problema), a tentativa mais recente é o estado atual.
    last = predictions.groupby(["student_id", "problem_id"], sort=False)[
        "predicted_correct_probability"
    ].last()

    matrix: dict[tuple[str, int], float] = {}
    # por (aluno, KC), as masteries dos problemas que ele tagueia
    by_student_kc: dict[tuple[str, int], list[float]] = {}
    for (student_id, problem_id), mastery in last.items():
        for kc_id in qmatrix.get(int(problem_id), []):
            by_student_kc.setdefault((student_id, kc_id), []).append(float(mastery))

    for key, values in by_student_kc.items():
        matrix[key] = sum(values) / len(values)
    return matrix
