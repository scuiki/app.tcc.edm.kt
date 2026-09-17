"""O seam público DataFrame-in/artifacts-out: `train_and_evaluate` (D-01).

A ordem das operações é load-bearing para a reprodutibilidade (Pitfall 2): build_sequences
(completo) → split → build_cache → build_train_vocab (train-only, CORE-04) → build_problem_index
(todos) → truncate (só fatia, CORE-05) → train → predict → AUC separado. O glue NUNCA reordena
esses passos — o teste de regressão é o oráculo que reprova qualquer troca.
"""

from __future__ import annotations

from typing import Callable, Mapping

import pandas as pd
import torch

from edmkt_core.evaluation import build_problem_index, compute_auc
from edmkt_core.features import build_cache
from edmkt_core.models.code_dkt import predict_code_dkt, train_code_dkt
from edmkt_core.pipeline.partitioning import build_train_vocab, split_by_subject
from edmkt_core.sequences import build_sequences, truncate_sequences


def _code_states_from_df(df: pd.DataFrame) -> dict[str, str]:
    # CodeStateID -> Code, last write wins (a CodeStateID maps to one snapshot).
    return dict(zip(df["CodeStateID"].astype(str), df["Code"].fillna("")))


def _csids(sequences: list[dict]) -> list[str]:
    out: list[str] = []
    for seq in sequences:
        out.extend(seq["events"]["CodeStateID"].astype(str).tolist())
    return out


def train_and_evaluate(
    df_or_train: pd.DataFrame,
    config: Mapping,
    test_df: pd.DataFrame | None = None,
    *,
    assignment_id: int,
    device: torch.device | None = None,
    on_epoch: Callable[[int, float], None] = lambda epoch, loss: None,
    n_workers: int | None = 1,
) -> dict:
    """Public DataFrame-in/artifacts-out entry for one assignment (CORE-01, CORE-05).

    Accepts EITHER a single DataFrame (split internally via split_by_subject at the
    TCC 1 random_state=1, Pitfall 3) OR an explicit train/test pair (Open Q2: Fase 3
    passes pre-split partitions; the regression test reproduces random_state=1). Either way
    the operation order below is fixed (Pitfall 2) and the vocab is built from train only.

    Returns {model, config, vocab, first_auc, all_auc, pred_df, n_train_events,
    n_test_events}. The caller owns seeding (set_global_seed) before invoking this.
    """
    if test_df is None:
        train_df, test_df = split_by_subject(df_or_train)
    else:
        train_df = df_or_train

    max_len = config.get("max_len", 50)
    R = config.get("R", 50)

    # 1. build_sequences (full) — is_first_attempt derived once per partition (plan 03).
    train_sequences = build_sequences(train_df, assignment_id)
    test_sequences = build_sequences(test_df, assignment_id)

    # 2. build_cache for train+test CodeStateIDs (Pitfall 5: n_workers safe for tests).
    code_states = _code_states_from_df(pd.concat([train_df, test_df], ignore_index=True))
    all_csids = sorted(set(_csids(train_sequences)) | set(_csids(test_sequences)))
    cache_raw = build_cache(
        all_csids, code_states,
        max_path_length=config.get("max_path_length", 8),
        max_path_width=config.get("max_path_width", 2),
        R=R, seed=config.get("seed", 42), n_workers=n_workers,
    )

    # 3. build_train_vocab — train-only, leakage-proof by construction (CORE-04).
    token_to_idx, path_to_idx = build_train_vocab(cache_raw, _csids(train_sequences))
    vocab = {
        "token_to_idx": token_to_idx,
        "path_to_idx": path_to_idx,
        "node_count": len(token_to_idx),
        "path_count": len(path_to_idx),
    }

    # 4. build_problem_index over ALL sequences (the M head spans every problem).
    problem_to_idx = build_problem_index(train_sequences + test_sequences)

    # 5. truncate (slice-only, carries is_first_attempt unchanged — CORE-05).
    train_sequences = truncate_sequences(train_sequences, max_len=max_len)
    test_sequences = truncate_sequences(test_sequences, max_len=max_len)

    # 6. train + predict (device/on_epoch injected — D-02).
    model = train_code_dkt(
        train_sequences, problem_to_idx, vocab, dict(config), cache_raw,
        seed=config.get("seed", 42), device=device, on_epoch=on_epoch,
    )
    pred_df = predict_code_dkt(
        model, test_sequences, problem_to_idx, vocab, cache_raw,
        max_len=max_len, R=R,
    )

    n_train_events = sum(min(len(s["events"]), max_len) for s in train_sequences)

    # 7. separated metrics (CORE-05): same compute_auc, the flag is the only difference.
    return {
        "model": model,
        "config": config,
        "vocab": vocab,
        "first_auc": compute_auc(pred_df, first_attempt_only=True),
        "all_auc": compute_auc(pred_df, first_attempt_only=False),
        "pred_df": pred_df,
        "n_train_events": n_train_events,
        "n_test_events": len(pred_df),
    }
