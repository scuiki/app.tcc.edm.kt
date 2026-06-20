"""edmkt_core public pipeline glue (DataFrame in / artifacts out).

The public seam (D-01): train_and_evaluate is the one entry the golden-run (plan 06)
and every later phase wrap. It takes a generic pre-validated ProgSnap2 DataFrame (no
CSEDM-specific path read, CORE-01) and returns a pure artifact dict — no filesystem,
SQLite, or FastAPI concern leaks across this boundary (D-03 state isolation).

Operation order is load-bearing for reproducibility (Pitfall 2): build_sequences (full)
-> split -> build_cache -> build_train_vocab (train-only, CORE-04) -> build_problem_index
(all) -> truncate (slice-only, CORE-05) -> train -> predict -> separated AUC. The glue
never reorders these steps.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Callable, Mapping

import pandas as pd
import torch
from sklearn.model_selection import train_test_split

from edmkt_core.evaluation import build_problem_index, compute_auc
from edmkt_core.features import build_cache, build_vocab
from edmkt_core.models.code_dkt import predict_code_dkt, train_code_dkt
from edmkt_core.sequences import build_sequences, truncate_sequences


def split_by_subject(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 1,  # Pitfall 3: TCC 1 partition uses random_state=1, NOT 42.
    min_attempts: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Partition events into train/test by student, disjoint by SubjectID.

    Extracted from tcc.edm.kt data_loader.load_spring2019_split (no CSV I/O, D-05):
    keep students with >= min_attempts Run.Program events, split the unique student
    set, then partition rows by membership so no SubjectID spans both partitions.
    """
    run = df[df["EventType"] == "Run.Program"]
    attempts = run.groupby("SubjectID").size()
    eligible = attempts[attempts >= min_attempts].index
    df_filtered = df[df["SubjectID"].isin(eligible)]

    students = df_filtered["SubjectID"].unique()
    train_s, test_s = train_test_split(
        students, test_size=test_size, random_state=random_state
    )

    train_df = df_filtered[df_filtered["SubjectID"].isin(train_s)].reset_index(drop=True)
    test_df = df_filtered[df_filtered["SubjectID"].isin(test_s)].reset_index(drop=True)
    return train_df, test_df


def build_train_vocab(
    cache_raw: dict[str, list[tuple[str, str, str]]],
    train_csids: Iterable[str],
) -> tuple[dict[str, int], dict[str, int]]:
    """Build the path vocabulary from the train partition's CodeStateIDs ONLY.

    The split-before-vocab contract (notebook 06 cell 14) promoted to code: subset
    the raw cache to train CodeStateIDs before calling build_vocab, so the vocab can
    never observe test-partition paths (CORE-04, T-01-05). Held-out tensorization
    then yields OOV>0 by construction.
    """
    train_csids = set(train_csids)
    cache_train = {c: cache_raw[c] for c in train_csids if c in cache_raw}
    return build_vocab(cache_train)


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
    passes pre-split partitions; the golden-run reproduces random_state=1). Either way
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
