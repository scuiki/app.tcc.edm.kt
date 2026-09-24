"""De previsões por problema para mastery por aluno × KC, através da Q-matrix.

O Code-DKT prevê por PROBLEMA (a saída do modelo tem uma posição por problem_id); o professor lê
por KC. A ponte é a Q-matrix: a mastery de um KC é a média das masteries dos problemas que ele
tagueia. Nunca indexar a saída do modelo por kc_id: ela é por problema.
"""

from __future__ import annotations

import pandas as pd


def aggregate_student_mastery(
    predictions: pd.DataFrame, qmatrix: dict[int, list[int]]
) -> dict[tuple[str, int], float]:
    """A matriz {(student_id, kc_id): mastery} a partir das previsões e da Q-matrix.

    A mastery de um problema é a ÚLTIMA `predicted_correct_probability` do par (aluno, problema);
    a de um KC é a média sobre os problemas que ele tagueia.
    """
    if predictions.empty:
        return {}

    # A última linha vence por (aluno, problema): a tentativa mais recente é o estado atual.
    last = predictions.groupby(["student_id", "problem_id"], sort=False)[
        "predicted_correct_probability"
    ].last()

    matrix: dict[tuple[str, int], float] = {}
    # por (aluno, KC): as masteries dos problemas que o KC tagueia
    by_student_kc: dict[tuple[str, int], list[float]] = {}
    for (student_id, problem_id), mastery in last.items():
        for kc_id in qmatrix.get(int(problem_id), []):
            by_student_kc.setdefault((student_id, kc_id), []).append(float(mastery))

    for key, values in by_student_kc.items():
        matrix[key] = sum(values) / len(values)
    return matrix
