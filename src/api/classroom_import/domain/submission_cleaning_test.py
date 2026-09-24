"""Testes do estágio C (clean): stream de eventos canônico.

Herméticos e CPU-only: constroem o cru sobre `a439_mini_progsnap` / `ingest_orphan_df`. Asseguram invariantes do
contrato (conjuntos de EventType/colunas, contagens), nunca valores mágicos de AUC.
"""

from __future__ import annotations

import pandas as pd

from api.classroom_import.domain.submission_cleaning import CLEANED_COLUMNS, clean_submissions
from api.classroom_import.domain.submission_event import KEPT_EVENTS

# code_states que cobre todos os CodeStateID do a439_mini, para a integridade não dropar nada
# nos testes de dedup/binarização (o órfão é exercitado à parte com ingest_orphan_df).
_A439_CODE_STATES = {f"c{i}": "x" for i in range(1, 7)} | {f"l{i}": "x" for i in range(1, 9)}


def _compile_plain_row(base_row: dict) -> dict:
    # Um Compile plain compartilha o timestamp do Run.Program e NUNCA carrega Score.
    row = dict(base_row)
    row["EventType"] = "Compile"
    row["Score"] = float("nan")
    return row


def test_dedup_drops_compile_plain_and_warns(a439_mini_progsnap):
    # Injeta Compile plain em cima de cada Run.Program (mesmo timestamp) — devem sumir pós-clean.
    rp = a439_mini_progsnap[a439_mini_progsnap["EventType"] == "Run.Program"]
    plains = pd.DataFrame([_compile_plain_row(r) for _, r in rp.iterrows()])
    raw = pd.concat([a439_mini_progsnap, plains], ignore_index=True)

    df, items = clean_submissions(raw, _A439_CODE_STATES)

    assert set(df["event_type"].unique()).issubset(KEPT_EVENTS)
    assert "Compile" not in set(df["event_type"].unique())

    dedup = [i for i in items if i.check == "dedup_compile"]
    assert len(dedup) == 1
    assert dedup[0].severity == "warning"
    assert dedup[0].count == len(plains)


def test_no_dedup_warning_when_no_compile_plain(a439_mini_progsnap):
    # a439_mini só tem Run.Program/Compile.Error — nada a descartar, nenhum aviso de dedup.
    df, items = clean_submissions(a439_mini_progsnap, _A439_CODE_STATES)
    assert set(df["event_type"].unique()).issubset(KEPT_EVENTS)
    assert [i for i in items if i.check == "dedup_compile"] == []


def test_is_correct_binarization_rule(a439_mini_progsnap):
    # is_correct = (Run.Program & Score==1.0); Compile.Error é sempre incorreto.
    df, _ = clean_submissions(a439_mini_progsnap, _A439_CODE_STATES)
    expected = ((df["event_type"] == "Run.Program") & (df["score"] == 1.0)).astype(int)
    assert (df["is_correct"] == expected).all()

    compile_err = df[df["event_type"] == "Compile.Error"]
    assert (compile_err["is_correct"] == 0).all()


def test_continuous_score_preserved(a439_mini_progsnap):
    # um Score contínuo (0.5) NÃO pode virar 0/1 na coluna Score.
    raw = a439_mini_progsnap.copy()
    raw.loc[raw.index[0], "Score"] = 0.5
    df, _ = clean_submissions(raw, _A439_CODE_STATES)
    assert 0.5 in set(df["score"].tolist())


def test_orphan_codestate_dropped_counted_and_warned(ingest_orphan_df):
    # ingest_orphan_df: code_states só tem {c1, c2}; "c_orphan" deve sumir, contado, virar warning.
    raw, code_states = ingest_orphan_df
    df, items = clean_submissions(raw, code_states)

    assert "c_orphan" not in set(df["code_snapshot_id"].astype(str))
    orphan = [i for i in items if i.check == "orphan_codestate"]
    assert len(orphan) == 1
    assert orphan[0].severity == "warning"
    assert orphan[0].count == 1


def test_orphan_warning_never_leaks_raw_code(ingest_orphan_df):
    # a mensagem/local do aviso carrega só contagem, nunca Code cru.
    raw, code_states = ingest_orphan_df
    _, items = clean_submissions(raw, code_states)
    for item in items:
        assert "public" not in item.message  # nenhum snippet Java vaza


def test_code_joined_for_valid_rows(ingest_orphan_df):
    # As linhas válidas têm Code preenchido pelo map de code_states (join por CodeStateID).
    raw, code_states = ingest_orphan_df
    df, _ = clean_submissions(raw, code_states)
    assert df["code"].notna().all()
    for _, row in df.iterrows():
        assert row["code"] == code_states[str(row["code_snapshot_id"])]


def test_canonical_columns_match_seam_contract(ingest_orphan_df):
    # O conjunto exato de colunas que ml consome, já com os nomes do glossário.
    raw, code_states = ingest_orphan_df
    df, _ = clean_submissions(raw, code_states)
    assert set(df.columns) == set(CLEANED_COLUMNS)
    assert list(df.columns) == CLEANED_COLUMNS
