"""Entrada do Code-DKT: cada tentativa vira o one-hot do DKT + os índices dos seus AST paths."""

# Portado do TCC 1 (src/code_features.py: paths_to_tensor, build_code_input_tensor).
# Numérica congelada; os testes de caracterização travam qualquer mudança.

from __future__ import annotations

import numpy as np
import torch
from torch import Tensor


def ast_paths_to_index_array(
    paths: list[tuple[str, str, str]],
    token_to_idx: dict[str, int],
    path_to_idx: dict[str, int],
    R: int = 50,
) -> np.ndarray:
    """Os paths de um snapshot como um array (R, 3) de índices, com zero-padding."""

    arr = np.zeros((R, 3), dtype=np.int64)
    for r, (start, path_str, end) in enumerate(paths[:R]):
        arr[r, 0] = token_to_idx.get(start, 0)
        arr[r, 1] = path_to_idx.get(path_str, 0)
        arr[r, 2] = token_to_idx.get(end, 0)
    return arr


def build_model_input_tensors(
    sequences: list[dict],
    ast_paths_by_snapshot: dict[str, list[tuple[str, str, str]]],
    token_to_idx: dict[str, int],
    path_to_idx: dict[str, int],
    problem_to_idx: dict[int, int],
    max_len: int = 50,
    R: int = 50,
) -> tuple[Tensor, Tensor, Tensor]:
    """X (one-hot do DKT + AST paths), Y_next (one-hot do próximo problema) e a máscara."""

    M = len(problem_to_idx)
    N = len(sequences)

    X = torch.zeros(N, max_len, 2 * M + R * 3, dtype=torch.float32)
    Y_next = torch.zeros(N, max_len, M, dtype=torch.float32)
    mask = torch.zeros(N, max_len, dtype=torch.bool)

    for i, seq in enumerate(sequences):
        events = seq["events"]
        if len(events) > max_len:
            events = events.iloc[-max_len:]
        L = len(events)
        pad = max_len - L  # left-padding offset (readdata.py: 'extra')

        pids = events["problem_id"].values
        corrects = events["is_correct"].values
        snapshot_ids = events["code_snapshot_id"].astype(str).values

        for t_rel in range(L):
            t = pad + t_rel
            m = problem_to_idx[int(pids[t_rel])]

            # DKT one-hot (Piech et al., 2015, Section 3)
            if corrects[t_rel]:
                X[i, t, m] = 1.0
            else:
                X[i, t, m + M] = 1.0

            # Code features: lookup pré-computado → (R, 3) → flatten float32
            raw_paths = ast_paths_by_snapshot.get(snapshot_ids[t_rel], [])
            code_arr = ast_paths_to_index_array(raw_paths, token_to_idx, path_to_idx, R)
            X[i, t, 2 * M :] = torch.from_numpy(code_arr.flatten().astype(np.float32))

            mask[i, t] = True

        # Y_next[t] = delta(q_{t+1}): one-hot do próximo problema
        for t_rel in range(L - 1):
            t = pad + t_rel
            m_next = problem_to_idx[int(pids[t_rel + 1])]
            Y_next[i, t, m_next] = 1.0

    return X, Y_next, mask
