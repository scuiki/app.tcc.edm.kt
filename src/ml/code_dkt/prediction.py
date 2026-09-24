"""Predição do Code-DKT: a probabilidade de acerto de cada próxima tentativa."""

# Portado do TCC 1 (src/models/code_dkt.py). Numérica congelada.

from __future__ import annotations

import pandas as pd
import torch

from ml.code_dkt.model import CodeDKTModel
from ml.code_dkt.model_input import build_model_input_tensors


def predict_code_dkt(
    model: CodeDKTModel,
    sequences: list[dict],
    problem_to_idx: dict[int, int],
    vocab: dict,
    ast_paths_by_snapshot: dict[str, list],
    max_len: int = 50,
    R: int = 50,
) -> pd.DataFrame:
    """Uma linha por tentativa (menos a primeira de cada aluno): a probabilidade prevista de acerto.

    Colunas: student_id, problem_id, is_correct, is_first_attempt, predicted_correct_probability.
    """

    if not sequences:
        return pd.DataFrame(
            columns=["student_id", "problem_id", "is_correct",
                     "is_first_attempt", "predicted_correct_probability"]
        )

    device = next(model.parameters()).device
    model.eval()

    with torch.no_grad():
        X, _Y_next, mask = build_model_input_tensors(
            sequences, ast_paths_by_snapshot,
            vocab["token_to_idx"], vocab["path_to_idx"],
            problem_to_idx, max_len=max_len, R=R,
        )
        y_pred_np = model(X.to(device)).cpu().numpy()

    rows = []
    for i, seq in enumerate(sequences):
        events = seq["events"]
        if len(events) > max_len:
            events = events.iloc[-max_len:]
        L = len(events)
        start_idx = max_len - L

        for t_rel in range(1, L):
            t_prev = start_idx + t_rel - 1
            row = events.iloc[t_rel]
            m = problem_to_idx[int(row["problem_id"])]
            rows.append({
                "student_id": str(seq["student_id"]),
                "problem_id": int(row["problem_id"]),
                "is_correct": int(row["is_correct"]),
                "is_first_attempt": bool(row["is_first_attempt"]),
                "predicted_correct_probability": float(y_pred_np[i, t_prev, m]),
            })

    return pd.DataFrame(rows)
