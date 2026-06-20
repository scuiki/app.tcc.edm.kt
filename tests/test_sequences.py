"""is_first_attempt immutability invariant through truncation (CORE-05).

The bug (RESEARCH Pitfall 1, +13.6pp first-attempt AUC inflation): the verbatim
port recomputes is_first_attempt on the truncated window, so a problem whose global
first attempt falls OUTSIDE the window has a later in-window occurrence wrongly
relabeled as a first attempt. These tests pin the corrected invariant: the flag is
derived once on the full ordered sequence and carried immutably through truncation.
"""

from __future__ import annotations

from edmkt_core.sequences import build_sequences, truncate_sequences


def _events_for(sequences, subject_id):
    return next(s["events"] for s in sequences if s["subject_id"] == subject_id)


def test_first_attempt_immutable(a439_mini):
    # S_long problems in order: [1,2,1,3,2,3,1,2]. With max_len=5 the window is the
    # last 5 events [3,2,3,1,2]; every one of those problems already appeared earlier
    # (global first OUTSIDE the window), so none is a true first attempt.
    sequences = build_sequences(a439_mini, 439)
    truncated = truncate_sequences(sequences, max_len=5)
    window = _events_for(truncated, "S_long")
    assert len(window) == 5
    assert window["is_first_attempt"].sum() == 0


def test_truncated_count_le_full(a439_mini):
    sequences = build_sequences(a439_mini, 439)
    truncated = truncate_sequences(sequences, max_len=5)
    for seq in sequences:
        full = seq["events"]["is_first_attempt"].sum()
        trunc = _events_for(truncated, seq["subject_id"])["is_first_attempt"].sum()
        assert trunc <= full


def test_no_recompute_preserves_column(a439_mini):
    # The flag on surviving rows must equal its value in the full sequence (carried,
    # not recomputed). CodeStateID uniquely identifies a row, so align on it.
    sequences = build_sequences(a439_mini, 439)
    truncated = truncate_sequences(sequences, max_len=5)
    for seq in sequences:
        full = seq["events"].set_index("CodeStateID")["is_first_attempt"]
        window = _events_for(truncated, seq["subject_id"])
        for csid, flag in zip(window["CodeStateID"], window["is_first_attempt"]):
            assert bool(flag) == bool(full.loc[csid])


def test_short_sequence_unchanged(a439_mini):
    # S1 has 3 events (< max_len): returned untouched, flag identical to build output.
    sequences = build_sequences(a439_mini, 439)
    truncated = truncate_sequences(sequences, max_len=5)
    before = _events_for(sequences, "S1")
    after = _events_for(truncated, "S1")
    assert len(after) == len(before)
    assert list(after["is_first_attempt"]) == list(before["is_first_attempt"])
