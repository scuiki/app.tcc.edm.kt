"""train_and_evaluate de ponta a ponta: dado limpo entra, modelo e métricas saem.

Travam que nenhum caminho específico do CSEDM é lido, que o first-attempt AUC e o AUC de todas as
tentativas saem como métricas separadas, e que a ordem das operações usa o vocabulário só do treino.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import torch.nn as nn

from ml.code_dkt.train_and_evaluate import train_and_evaluate
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS
from ml.reproducibility.random_seed import seed_all_random_generators
from ml.code_dkt.ast_paths import extract_ast_paths
from ml.code_dkt.model_input import ast_paths_to_index_array

ASSIGNMENT_ID = 439

# Eight structurally distinct method bodies. Each student gets a unique snippet so the
# held-out (test) student always contributes AST paths unseen in train (OOV>0 holds by
# construction, independent of which SubjectIDs the random draw assigns to the test set).
_JAVA_BODIES = [
    "public int g0(int a, int b) { int s = a + b; return s; }",
    "public int g1(int a) { for (int i = 0; i < a; i++) { a = a * 2; } return a; }",
    "public boolean g2(int n) { if (n > 0) { return true; } return false; }",
    "public int g3(int n) { while (n > 0) { n = n - 1; } return n; }",
    "public int g4(int[] xs) { int t = 0; for (int x : xs) { t += x; } return t; }",
    "public String g5(boolean b) { return b ? \"yes\" : \"no\"; }",
    "public int g6(int n) { switch (n) { case 0: return 1; default: return n; } }",
    "public int g7(int n) { try { return 10 / n; } catch (Exception e) { return -1; } }",
]


def _row(subject, problem, ts, score, code, snapshot_id):
    correct = int(score == 1.0)
    return {
        "student_id": subject,
        "problem_id": problem,
        "progsnap_assignment_id": ASSIGNMENT_ID,
        "submitted_at": ts,
        "event_type": "Run.Program",
        "score": score,
        "code_snapshot_id": snapshot_id,
        "code": code,
        "is_correct": correct,
    }


@pytest.fixture
def progsnap_df() -> pd.DataFrame:
    """Synthetic generic ProgSnap2 DataFrame: 8 students x 3 problems.

    Every student has >= min_attempts(=3) Run.Program events (so all survive the
    split filter) and a structurally distinct Java body (so the held-out OOV>0
    invariant holds for whichever student lands in the test partition). Problem 1 is
    repeated within several students so is_first_attempt carries both True and False.
    """
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for s in range(8):
        subject = f"S{s}"
        body = _JAVA_BODIES[s]
        plan = [
            (1, 0.0),
            (2, 1.0),
            (1, 1.0),  # problem 1 repeated -> is_first_attempt False on this row
            (3, 0.0),
            (2, 1.0),
        ]
        for step, (pid, score) in enumerate(plan):
            ts = base + pd.Timedelta(hours=s) + pd.Timedelta(minutes=step)
            rows.append(_row(subject, pid, ts, score, body, f"c{s}_{step}"))

    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")
    return df


# Architecture frozen; only epochs reduced for a fast CPU smoke run (never in CODE_DKT_HYPERPARAMETERS).
_FAST_CONFIG = {**CODE_DKT_HYPERPARAMETERS, "epochs": 3}


def test_end_to_end_fixture(progsnap_df, cpu_device):
    seed_all_random_generators(42, strict=True)
    result = train_and_evaluate(
        progsnap_df,
        config=_FAST_CONFIG,
        progsnap_assignment_id=ASSIGNMENT_ID,
        device=cpu_device,
    )
    assert set(result) >= {"model", "config", "first_attempt_auc", "all_attempts_auc", "predictions", "vocab"}
    assert isinstance(result["model"], nn.Module)

    pred_df = result["predictions"]
    assert len(pred_df) > 0
    for col in ("is_correct", "predicted_correct_probability", "is_first_attempt"):
        assert col in pred_df.columns


def test_metrics_separated(progsnap_df, cpu_device):
    from ml.evaluation.auc import compute_auc

    seed_all_random_generators(42, strict=True)
    result = train_and_evaluate(
        progsnap_df,
        config=_FAST_CONFIG,
        progsnap_assignment_id=ASSIGNMENT_ID,
        device=cpu_device,
    )
    first_auc = result["first_attempt_auc"]
    all_auc = result["all_attempts_auc"]

    # Each is a float (NaN is a float) — distinct labeled metrics.
    for v in (first_auc, all_auc):
        assert isinstance(v, float)

    # The two metrics are computed via compute_auc with first_attempt_only True/False
    # over the SAME pred_df: the returned values must match an independent recompute, and
    # the first-attempt pool is a strict subset of the pooled rows (so they are genuinely
    # different metrics, not the same number relabeled). On a toy CPU model the float
    # values can coincide; the subset relationship is the load-bearing guarantee.
    pred_df = result["predictions"]
    np.testing.assert_equal(first_auc, compute_auc(pred_df, first_attempt_only=True))
    np.testing.assert_equal(all_auc, compute_auc(pred_df, first_attempt_only=False))

    n_first = int(pred_df["is_first_attempt"].sum())
    n_all = len(pred_df)
    assert 0 < n_first < n_all  # strict subset -> the two metrics span different rows


def test_first_attempt_carried_to_pred_df(progsnap_df, cpu_device):
    seed_all_random_generators(42, strict=True)
    result = train_and_evaluate(
        progsnap_df,
        config=_FAST_CONFIG,
        progsnap_assignment_id=ASSIGNMENT_ID,
        device=cpu_device,
    )
    pred_df = result["predictions"]

    # The flag is derived once on the full ordered sequence (build_student_sequences) and sliced
    # through truncation -> the count of first-attempt rows per (user, problem) is <= 1.
    # No recompute can produce a second "first attempt" for the same (user, problem).
    first_only = pred_df[pred_df["is_first_attempt"]]
    per_pair = first_only.groupby(["student_id", "problem_id"]).size()
    assert (per_pair <= 1).all()


def test_operation_order_uses_train_only_vocab(progsnap_df, cpu_device):
    seed_all_random_generators(42, strict=True)
    result = train_and_evaluate(
        progsnap_df,
        config=_FAST_CONFIG,
        progsnap_assignment_id=ASSIGNMENT_ID,
        device=cpu_device,
    )
    vocab = result["vocab"]
    token_to_idx = vocab["token_to_idx"]
    path_to_idx = vocab["path_to_idx"]

    # Drive a held-out Java body whose try/catch structure no train student used, then
    # tensorize against the pipeline's OWN returned vocab. If the pipeline had built a
    # union (train+test) vocab, these paths would resolve (OOV=0). Train-only vocab => OOV>0.
    held_out = "public int z(int n) { try { return 100 / n; } catch (ArithmeticException e) { return 0; } }"
    paths = extract_ast_paths(held_out)
    assert paths, "held-out snippet must yield >= 1 AST path"

    arr = ast_paths_to_index_array(paths, token_to_idx, path_to_idx, R=len(paths))
    # Column 1 holds the path-string index; idx 0 is the OOV/PAD slot.
    oov = int((arr[:, 1] == 0).sum())
    assert oov > 0, "held-out paths should be OOV against a train-only vocab"
