"""build_student_sequences / truncate_student_sequences.

Caracterização do comportamento portado do TCC 1 e a invariante que corrige o bug do port literal:
`is_first_attempt` é marcado uma vez na sequência completa e carregado intacto pelo truncamento.
Recalculá-lo na janela reetiquetava como primeira tentativa uma ocorrência posterior de um problema
cuja primeira tentativa real ficou fora da janela (+13,6 pontos de first-attempt AUC inflado).
"""

from __future__ import annotations

from ml.code_dkt.student_sequences import build_student_sequences, truncate_student_sequences


def test_build_sequences_returns_one_dict_per_student(a439_mini):
    sequences = build_student_sequences(a439_mini, 439)
    subject_ids = {seq["student_id"] for seq in sequences}
    assert subject_ids == {"S1", "S2", "S_long"}
    for seq in sequences:
        assert seq["progsnap_assignment_id"] == 439
        assert "is_first_attempt" in seq["events"].columns


def test_build_sequences_first_attempt_has_true_and_false(a439_mini):
    # Repeated problems in the fixture produce both first (True) and repeat (False).
    sequences = build_student_sequences(a439_mini, 439)
    flags = set()
    for seq in sequences:
        flags.update(bool(v) for v in seq["events"]["is_first_attempt"])
    assert flags == {True, False}


def test_truncate_keeps_at_most_max_len_events(a439_mini):
    sequences = build_student_sequences(a439_mini, 439)
    truncated = truncate_student_sequences(sequences, max_len=5)
    for seq in truncated:
        assert len(seq["events"]) <= 5


def test_truncate_first_attempt_counts(a439_mini):
    # Plan 03 deliberately replaced the old buggy baseline: the prior
    # assertion (trunc["S_long"] >= 1) pinned the documented +13.6pp inflation bug,
    # where the in-window recompute relabeled global 2nd-occurrences as first attempts.
    # The corrected invariant slices only, so the flag is carried, never recomputed.
    sequences = build_student_sequences(a439_mini, 439)
    full = {s["student_id"]: s["events"]["is_first_attempt"].sum() for s in sequences}
    truncated = truncate_student_sequences(sequences, max_len=5)
    trunc = {s["student_id"]: s["events"]["is_first_attempt"].sum() for s in truncated}

    # Untruncated students keep their counts unchanged.
    assert trunc["S1"] == full["S1"]
    assert trunc["S2"] == full["S2"]
    # S_long's last-5 window [3,2,3,1,2]: only P3's global-first (l4) lands inside the
    # window, so the carried count is 1 — vs the old buggy in-window recompute of 3.
    assert trunc["S_long"] == 1


def _events_for(sequences, subject_id):
    return next(s["events"] for s in sequences if s["student_id"] == subject_id)


def test_first_attempt_immutable(a439_mini):
    # S_long problems in order: [1,2,1,3,2,3,1,2]. With max_len=5 the window is the
    # last 5 events [3,2,3,1,2] (CodeStateIDs l4..l8). P2 and P1 in the window are
    # global repeats (their first attempt is OUTSIDE the window) and must stay False;
    # P3's first global attempt (l4) happens to fall inside the window, so it stays
    # True. The buggy in-window recompute instead flips l5 (P2) and l7 (P1) to True.
    sequences = build_student_sequences(a439_mini, 439)
    truncated = truncate_student_sequences(sequences, max_len=5)
    window = _events_for(truncated, "S_long").set_index("code_snapshot_id")["is_first_attempt"]
    assert len(window) == 5
    assert bool(window.loc["l5"]) is False  # P2 global-first (l2) outside window
    assert bool(window.loc["l7"]) is False  # P1 global-first (l1) outside window
    assert bool(window.loc["l4"]) is True   # P3 global-first is inside the window
    assert window.sum() == 1


def test_truncated_count_le_full(a439_mini):
    sequences = build_student_sequences(a439_mini, 439)
    truncated = truncate_student_sequences(sequences, max_len=5)
    for seq in sequences:
        full = seq["events"]["is_first_attempt"].sum()
        trunc = _events_for(truncated, seq["student_id"])["is_first_attempt"].sum()
        assert trunc <= full


def test_no_recompute_preserves_column(a439_mini):
    # The flag on surviving rows must equal its value in the full sequence (carried,
    # not recomputed). CodeStateID uniquely identifies a row, so align on it.
    sequences = build_student_sequences(a439_mini, 439)
    truncated = truncate_student_sequences(sequences, max_len=5)
    for seq in sequences:
        full = seq["events"].set_index("code_snapshot_id")["is_first_attempt"]
        window = _events_for(truncated, seq["student_id"])
        for snapshot_id, flag in zip(window["code_snapshot_id"], window["is_first_attempt"]):
            assert bool(flag) == bool(full.loc[snapshot_id])


def test_short_sequence_unchanged(a439_mini):
    # S1 has 3 events (< max_len): returned untouched, flag identical to build output.
    sequences = build_student_sequences(a439_mini, 439)
    truncated = truncate_student_sequences(sequences, max_len=5)
    before = _events_for(sequences, "S1")
    after = _events_for(truncated, "S1")
    assert len(after) == len(before)
    assert list(after["is_first_attempt"]) == list(before["is_first_attempt"])
