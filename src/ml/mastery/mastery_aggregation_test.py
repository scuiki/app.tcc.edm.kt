# A mastery de um KC é a média das masteries dos problemas que ele tagueia.

from __future__ import annotations

import pandas as pd
import pytest

from ml.mastery.mastery_aggregation import aggregate_student_mastery


def test_matrix_aggregates_problem_to_kc_by_mean():
    # Q-matrix liga KC1 aos problemas 1 e 3, e KC2 aos problemas 2 e 3.

    # A ÚLTIMA linha por (aluno, problema) vale como mastery final, não a 1ª tentativa.
    pred_df = pd.DataFrame(
        [
            {"student_id": "S1", "problem_id": 1, "is_correct": 0, "is_first_attempt": True,  "predicted_correct_probability": 0.9},
            {"student_id": "S1", "problem_id": 1, "is_correct": 0, "is_first_attempt": False, "predicted_correct_probability": 0.2},
            {"student_id": "S1", "problem_id": 2, "is_correct": 1, "is_first_attempt": True,  "predicted_correct_probability": 0.8},
            {"student_id": "S1", "problem_id": 3, "is_correct": 1, "is_first_attempt": True,  "predicted_correct_probability": 0.6},
        ]
    )
    qmatrix = {1: [10], 2: [20], 3: [10, 20]}  # problem_id -> [kc_id...]; KC1=10, KC2=20

    matrix = aggregate_student_mastery(pred_df, qmatrix)

    # matriz indexável por (student_id, kc_id) -> mastery float em [0,1].
    assert matrix[("S1", 10)] == pytest.approx(0.4)  # média(0.2 [última do prob1], 0.6)
    assert matrix[("S1", 20)] == pytest.approx(0.7)  # média(0.8, 0.6)
