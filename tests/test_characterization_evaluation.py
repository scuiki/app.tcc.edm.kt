"""Characterization tests for edmkt_core.evaluation (D-04, CORE-06).

Pin compute_auc's first/all separation (base for CORE-05) and its single-class/empty
NaN guard.
"""

from __future__ import annotations

import math

import pandas as pd

from edmkt_core.evaluation import compute_auc


def _pred_df():
    # Mix of first-attempt and repeat rows with both correct classes, so first-only
    # and all-rows AUC differ.
    return pd.DataFrame(
        [
            {"correct": 1, "is_first_attempt": True, "correct_predictions": 0.9},
            {"correct": 0, "is_first_attempt": True, "correct_predictions": 0.2},
            {"correct": 1, "is_first_attempt": True, "correct_predictions": 0.4},
            {"correct": 0, "is_first_attempt": False, "correct_predictions": 0.8},
            {"correct": 1, "is_first_attempt": False, "correct_predictions": 0.3},
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
            {"correct": 1, "is_first_attempt": True, "correct_predictions": 0.9},
            {"correct": 1, "is_first_attempt": True, "correct_predictions": 0.5},
        ]
    )
    assert math.isnan(compute_auc(df))


def test_empty_input_returns_nan():
    df = pd.DataFrame(
        {"correct": [], "is_first_attempt": [], "correct_predictions": []}
    )
    assert math.isnan(compute_auc(df))
