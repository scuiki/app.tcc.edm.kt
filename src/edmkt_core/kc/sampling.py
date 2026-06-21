# Ported from tcc.edm.kt — notebooks/03b_kc_generation.ipynb cell 4 (load_correct_samples +
# _bucket_for + diversity_sample). Frozen science (KC-01, Pitfall 4): per (subject, problem) take
# the FIRST correct submission chronologically, stratify by attempts-before into 5 buckets, and
# diversity-sample up to n=5. Pure: operates on the canonical DataFrame (Code/ProblemID/CodeStateID/
# correct), no I/O, no LLM — the app feeds it the cleaned Parquet.

from __future__ import annotations

import random

import pandas as pd

SEED = 42


def _bucket_for(total_attempts: int) -> int:
    """Map total attempts to one of 5 diversity buckets (Duan et al., 2025)."""
    if total_attempts <= 1:
        return 1
    if total_attempts <= 3:
        return 2
    if total_attempts <= 6:
        return 3
    if total_attempts <= 10:
        return 4
    return 5


def _first_correct_per_subject(problem_df: pd.DataFrame) -> list[dict]:
    """First correct submission per SubjectID for one problem, with attempts-before counted.

    Never returns incorrect code (Pitfall 4): a subject with no correct submission is skipped.
    """
    events = problem_df.sort_values("ServerTimestamp", kind="stable")
    samples: list[dict] = []
    for _subject_id, subject_events in events.groupby("SubjectID", sort=False):
        subject_events = subject_events.sort_values("ServerTimestamp", kind="stable")
        correct_mask = subject_events["correct"] == 1
        if not correct_mask.any():
            continue
        first_correct_pos = int(correct_mask.values.argmax())  # attempts BEFORE the first correct
        first_correct = subject_events.iloc[first_correct_pos]
        samples.append({
            "subject_id": str(_subject_id),
            "codestate_id": str(first_correct["CodeStateID"]),
            "total_attempts": first_correct_pos + 1,
            "code": str(first_correct["Code"]),
        })
    return samples


def diversity_sample(problem_df: pd.DataFrame, n: int = 5,
                     rng: random.Random | None = None) -> list[dict]:
    """≤n first-correct samples for one problem, stratified across the 5 attempt buckets.

    Walks buckets 1..5 (direct-solution strategies first), drawing one sample per non-empty
    bucket until n is reached. RNG is seeded for reproducibility (frozen science).
    """
    if rng is None:
        rng = random.Random(SEED)

    correct_events = _first_correct_per_subject(problem_df)

    buckets: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    for event in correct_events:
        buckets[_bucket_for(int(event["total_attempts"]))].append(event)

    sampled: list[dict] = []
    for b in (1, 2, 3, 4, 5):
        if len(sampled) >= n:
            break
        if buckets[b]:
            sampled.append(rng.choice(buckets[b]))
    return sampled
