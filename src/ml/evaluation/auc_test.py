"""compute_auc: first-attempt e todas as tentativas são métricas distintas; uma classe só ou
nenhuma linha devolvem NaN.
"""

from __future__ import annotations

import math

import pandas as pd

from ml.evaluation.auc import compute_auc


def _pred_df():
    # Mix of first-attempt and repeat rows with both correct classes, so first-only
    # and all-rows AUC differ.
    return pd.DataFrame(
        [
            {"is_correct": 1, "is_first_attempt": True, "predicted_correct_probability": 0.9},
            {"is_correct": 0, "is_first_attempt": True, "predicted_correct_probability": 0.2},
            {"is_correct": 1, "is_first_attempt": True, "predicted_correct_probability": 0.4},
            {"is_correct": 0, "is_first_attempt": False, "predicted_correct_probability": 0.8},
            {"is_correct": 1, "is_first_attempt": False, "predicted_correct_probability": 0.3},
        ]
    )


def test_first_and_all_metrics_are_distinct():
    df = _pred_df()
    first = compute_auc(df, first_attempt_only=True)
    allr = compute_auc(df, first_attempt_only=False)
    assert isinstance(first, float) and isinstance(allr, float)
    assert first != allr


def test_single_class_input_returns_nan():
    # Only one class present -> roc_auc undefined -> NaN guard.
    df = pd.DataFrame(
        [
            {"is_correct": 1, "is_first_attempt": True, "predicted_correct_probability": 0.9},
            {"is_correct": 1, "is_first_attempt": True, "predicted_correct_probability": 0.5},
        ]
    )
    assert math.isnan(compute_auc(df))


def test_empty_input_returns_nan():
    df = pd.DataFrame(
        {"is_correct": [], "is_first_attempt": [], "predicted_correct_probability": []}
    )
    assert math.isnan(compute_auc(df))
