"""A mastery de um KC é a média das masteries dos problemas que ele tagueia."""

from __future__ import annotations

import pandas as pd
import pytest

from ml.mastery.mastery_aggregation import aggregate_student_mastery


def test_matrix_aggregates_problem_to_kc_by_mean():
    # A mastery de um KC é a MÉDIA das masteries dos problemas que o KC
    # marca. Q-matrix: KC1 → {prob 1, prob 3}; KC2 → {prob 2, prob 3}.
    # Para um aluno com problem-mastery {1: 0.2, 2: 0.8, 3: 0.6}:
    #   KC1 = mean(0.2, 0.6) = 0.4 ; KC2 = mean(0.8, 0.6) = 0.7.
    # previsões no formato de predict_code_dkt: a ÚLTIMA linha por (aluno, problema) é a mastery
    # final daquele problema; uma 1ª tentativa anterior NÃO deve sobrescrever a última.
    pred_df = pd.DataFrame(
        [
            {"student_id": "S1", "problem_id": 1, "is_correct": 0, "is_first_attempt": True,  "predicted_correct_probability": 0.9},
            {"student_id": "S1", "problem_id": 1, "is_correct": 0, "is_first_attempt": False, "predicted_correct_probability": 0.2},  # última p/ prob 1
            {"student_id": "S1", "problem_id": 2, "is_correct": 1, "is_first_attempt": True,  "predicted_correct_probability": 0.8},
            {"student_id": "S1", "problem_id": 3, "is_correct": 1, "is_first_attempt": True,  "predicted_correct_probability": 0.6},
        ]
    )
    qmatrix = {1: [10], 2: [20], 3: [10, 20]}  # problem_id -> [kc_id...]; KC1=10, KC2=20

    matrix = aggregate_student_mastery(pred_df, qmatrix)

    # matriz indexável por (student_id, kc_id) -> mastery float em [0,1].
    assert matrix[("S1", 10)] == pytest.approx(0.4)  # mean(0.2 [última do prob1], 0.6)
    assert matrix[("S1", 20)] == pytest.approx(0.7)  # mean(0.8, 0.6)
