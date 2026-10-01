# Predição do Code-DKT, a probabilidade de acerto de cada próxima tentativa.

# Portado do TCC 1 (src/models/code_dkt.py).

from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from ml.code_dkt.model import CodeDKTModel
from ml.code_dkt.model_input import build_model_input_tensors

# Alunos por forward, o mesmo pedaço do treino, para nenhum forward passar do pico dele na GPU
INFERENCE_CHUNK_SIZE = 64


def _predict_in_chunks(
    model: CodeDKTModel,
    sequences: list[dict],
    problem_to_idx: dict[int, int],
    vocab: dict,
    ast_paths_by_snapshot: dict[str, list],
    max_len: int,
    R: int,
    path_sampling_seed: int,
) -> np.ndarray:
    # A saída (N, max_len, M) de todos os alunos, um pedaço de INFERENCE_CHUNK_SIZE por vez
    device = next(model.parameters()).device
    model.eval()
    outputs = []
    with torch.no_grad():
        for start in range(0, len(sequences), INFERENCE_CHUNK_SIZE):
            X, _Y_next, _mask = build_model_input_tensors(
                sequences[start : start + INFERENCE_CHUNK_SIZE], ast_paths_by_snapshot,
                vocab["token_to_idx"], vocab["path_to_idx"],
                problem_to_idx, max_len=max_len, R=R, path_sampling_seed=path_sampling_seed,
            )
            outputs.append(model(X.to(device)).cpu().numpy())
    return np.concatenate(outputs)


def predict_code_dkt(
    model: CodeDKTModel,
    sequences: list[dict],
    problem_to_idx: dict[int, int],
    vocab: dict,
    ast_paths_by_snapshot: dict[str, list],
    max_len: int = 50,
    R: int = 100,
    path_sampling_seed: int = 42,
) -> pd.DataFrame:
    # Uma linha por tentativa (exceto a 1ª de cada aluno), com a probabilidade prevista de acerto.

    if not sequences:
        return pd.DataFrame(
            columns=["student_id", "problem_id", "is_correct",
                     "is_first_attempt", "predicted_correct_probability"]
        )

    y_pred_np = _predict_in_chunks(
        model, sequences, problem_to_idx, vocab, ast_paths_by_snapshot,
        max_len, R, path_sampling_seed,
    )

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


def predict_current_state(
    model: CodeDKTModel,
    sequences: list[dict],
    problem_to_idx: dict[int, int],
    vocab: dict,
    ast_paths_by_snapshot: dict[str, list],
    max_len: int = 50,
    R: int = 100,
    path_sampling_seed: int = 42,
) -> pd.DataFrame:
    # Uma linha por aluno x problema, a chance de acerto se ele tentasse agora (último passo).

    if not sequences:
        return pd.DataFrame(columns=["student_id", "problem_id", "predicted_correct_probability"])

    y_pred_np = _predict_in_chunks(
        model, sequences, problem_to_idx, vocab, ast_paths_by_snapshot,
        max_len, R, path_sampling_seed,
    )

    rows = []
    for i, seq in enumerate(sequences):
        # Preenchimento à esquerda, então a última posição é sempre o passo final.
        for problem_id, m in problem_to_idx.items():
            rows.append({
                "student_id": str(seq["student_id"]),
                "problem_id": int(problem_id),
                "predicted_correct_probability": float(y_pred_np[i, max_len - 1, m]),
            })

    return pd.DataFrame(rows)
