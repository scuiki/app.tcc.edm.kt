"""Characterization tests for edmkt_core.sequences (D-04, CORE-06).

Pin CURRENT behavior of build_sequences / truncate_sequences. IMPORTANT: this does
NOT yet assert the is_first_attempt immutability invariant — that is plan 03's failing
test (CORE-05). Here we only characterize the verbatim (buggy) truncation.
"""

from __future__ import annotations

from edmkt_core.sequences import build_sequences, truncate_sequences


def test_build_sequences_returns_one_dict_per_student(a439_mini):
    sequences = build_sequences(a439_mini, 439)
    subject_ids = {seq["subject_id"] for seq in sequences}
    assert subject_ids == {"S1", "S2", "S_long"}
    for seq in sequences:
        assert seq["assignment_id"] == 439
        assert "is_first_attempt" in seq["events"].columns


def test_build_sequences_first_attempt_has_true_and_false(a439_mini):
    # Repeated problems in the fixture produce both first (True) and repeat (False).
    sequences = build_sequences(a439_mini, 439)
    flags = set()
    for seq in sequences:
        flags.update(bool(v) for v in seq["events"]["is_first_attempt"])
    assert flags == {True, False}


def test_truncate_keeps_at_most_max_len_events(a439_mini):
    sequences = build_sequences(a439_mini, 439)
    truncated = truncate_sequences(sequences, max_len=5)
    for seq in truncated:
        assert len(seq["events"]) <= 5


def test_truncate_first_attempt_counts(a439_mini):
    # Plan 03 (CORE-05) deliberately replaced the old buggy baseline: the prior
    # assertion (trunc["S_long"] >= 1) pinned the documented +13.6pp inflation bug,
    # where the in-window recompute relabeled global 2nd-occurrences as first attempts.
    # The corrected invariant slices only, so the flag is carried, never recomputed.
    sequences = build_sequences(a439_mini, 439)
    full = {s["subject_id"]: s["events"]["is_first_attempt"].sum() for s in sequences}
    truncated = truncate_sequences(sequences, max_len=5)
    trunc = {s["subject_id"]: s["events"]["is_first_attempt"].sum() for s in truncated}

    # Untruncated students keep their counts unchanged.
    assert trunc["S1"] == full["S1"]
    assert trunc["S2"] == full["S2"]
    # S_long's last-5 window [3,2,3,1,2]: only P3's global-first (l4) lands inside the
    # window, so the carried count is 1 — vs the old buggy in-window recompute of 3.
    assert trunc["S_long"] == 1
