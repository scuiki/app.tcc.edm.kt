# Caracterização de build/truncate_student_sequences; is_first_attempt não é recalculado na janela.

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
    # Problemas repetidos na fixture produzem tentativa 1ª (True) e repetida (False).
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
    # Antes fixava o bug de +13,6pp; agora garante que a janela só fatia, nunca recalcula.
    sequences = build_student_sequences(a439_mini, 439)
    full = {s["student_id"]: s["events"]["is_first_attempt"].sum() for s in sequences}
    truncated = truncate_student_sequences(sequences, max_len=5)
    trunc = {s["student_id"]: s["events"]["is_first_attempt"].sum() for s in truncated}

    # Alunos não truncados mantêm as contagens.
    assert trunc["S1"] == full["S1"]
    assert trunc["S2"] == full["S2"]
    # Janela [3,2,3,1,2] de S_long, só P3 (l4) é 1ª global dentro dela, contagem correta é 1.
    assert trunc["S_long"] == 1


def _events_for(sequences, subject_id):
    return next(s["events"] for s in sequences if s["student_id"] == subject_id)


def test_first_attempt_immutable(a439_mini):
    # S_long, problemas [1,2,1,3,2,3,1,2]; janela max_len=5 é [3,2,3,1,2] (l4..l8).
    sequences = build_student_sequences(a439_mini, 439)
    truncated = truncate_student_sequences(sequences, max_len=5)
    window = _events_for(truncated, "S_long").set_index("code_snapshot_id")["is_first_attempt"]
    assert len(window) == 5
    assert bool(window.loc["l5"]) is False  # P2, 1ª global (l2) fica fora da janela
    assert bool(window.loc["l7"]) is False  # P1, 1ª global (l1) fica fora da janela
    assert bool(window.loc["l4"]) is True   # P3, 1ª global cai dentro da janela
    assert window.sum() == 1


def test_truncated_count_le_full(a439_mini):
    sequences = build_student_sequences(a439_mini, 439)
    truncated = truncate_student_sequences(sequences, max_len=5)
    for seq in sequences:
        full = seq["events"]["is_first_attempt"].sum()
        trunc = _events_for(truncated, seq["student_id"])["is_first_attempt"].sum()
        assert trunc <= full


def test_no_recompute_preserves_column(a439_mini):
    # A flag nas linhas sobreviventes bate com a sequência completa, é carregada, não recalculada.
    sequences = build_student_sequences(a439_mini, 439)
    truncated = truncate_student_sequences(sequences, max_len=5)
    for seq in sequences:
        full = seq["events"].set_index("code_snapshot_id")["is_first_attempt"]
        window = _events_for(truncated, seq["student_id"])
        for snapshot_id, flag in zip(window["code_snapshot_id"], window["is_first_attempt"]):
            assert bool(flag) == bool(full.loc[snapshot_id])


def test_short_sequence_unchanged(a439_mini):
    # S1 tem 3 eventos (menos que max_len), volta intacto, flag igual ao output do build.
    sequences = build_student_sequences(a439_mini, 439)
    truncated = truncate_student_sequences(sequences, max_len=5)
    before = _events_for(sequences, "S1")
    after = _events_for(truncated, "S1")
    assert len(after) == len(before)
    assert list(after["is_first_attempt"]) == list(before["is_first_attempt"])
