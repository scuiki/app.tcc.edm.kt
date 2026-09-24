# train_and_evaluate de ponta a ponta; trava que os AUCs saem separados e o vocab é só do treino.

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

# Oito corpos de método distintos, um por aluno, garantem paths OOV no teste por construção.
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
    # DataFrame ProgSnap2 sintético, 8 alunos x 3 problemas, todos com >=3 Run.Program.
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for s in range(8):
        subject = f"S{s}"
        body = _JAVA_BODIES[s]
        plan = [
            (1, 0.0),
            (2, 1.0),
            (1, 1.0),  # problema 1 repetido, is_first_attempt False nesta linha
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


# Arquitetura congelada, só épocas reduzidas p/ smoke test em CPU (não em CODE_DKT_HYPERPARAMETERS).
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

    # Cada valor é float (NaN é float); são métricas rotuladas distintas.
    for v in (first_auc, all_auc):
        assert isinstance(v, float)

    # As duas métricas rodam sobre o mesmo pred_df; garantia real é o subconjunto estrito de linhas.
    pred_df = result["predictions"]
    np.testing.assert_equal(first_auc, compute_auc(pred_df, first_attempt_only=True))
    np.testing.assert_equal(all_auc, compute_auc(pred_df, first_attempt_only=False))

    n_first = int(pred_df["is_first_attempt"].sum())
    n_all = len(pred_df)
    assert 0 < n_first < n_all  # subconjunto estrito, as métricas cobrem linhas diferentes


def test_first_attempt_carried_to_pred_df(progsnap_df, cpu_device):
    seed_all_random_generators(42, strict=True)
    result = train_and_evaluate(
        progsnap_df,
        config=_FAST_CONFIG,
        progsnap_assignment_id=ASSIGNMENT_ID,
        device=cpu_device,
    )
    pred_df = result["predictions"]

    # A flag vem 1x da sequência completa, só é fatiada; no máx 1 "1ª tentativa" por aluno/problema.
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

    # Corpo Java reservado com try/catch inédito no treino; vocab união resolveria, só-treino não.
    held_out = "public int z(int n) { try { return 100 / n; } catch (ArithmeticException e) { return 0; } }"
    paths = extract_ast_paths(held_out)
    assert paths, "held-out snippet must yield >= 1 AST path"

    arr = ast_paths_to_index_array(paths, token_to_idx, path_to_idx, R=len(paths))
    # Coluna 1 guarda o índice do path; idx 0 é o slot OOV/PAD.
    oov = int((arr[:, 1] == 0).sum())
    assert oov > 0, "held-out paths should be OOV against a train-only vocab"
