"""Testes do estágio C (clean): stream de eventos canônico (D-10/D-11/D-12).

Herméticos e CPU-only: constroem o cru sobre `a439_mini` / `ingest_orphan_df` (Pitfall 2 —
órfão tem 0 cobertura no golden, então a fixture é sintética). Asseguram invariantes do
contrato (conjuntos de EventType/colunas, contagens), nunca valores mágicos de AUC.
"""

from __future__ import annotations

import pandas as pd

from edmkt_app.ingestion.clean import ALLOWED_EVENTS, clean_event_stream

# code_states que cobre todos os CodeStateID do a439_mini, para a integridade não dropar nada
# nos testes de dedup/binarização (o órfão é exercitado à parte com ingest_orphan_df).
_A439_CODE_STATES = {f"c{i}": "x" for i in range(1, 7)} | {f"l{i}": "x" for i in range(1, 9)}


def _compile_plain_row(base_row: dict) -> dict:
    # Um Compile plain compartilha o timestamp do Run.Program e NUNCA carrega Score (D-10).
    row = dict(base_row)
    row["EventType"] = "Compile"
    row["Score"] = float("nan")
    row["correct"] = 0
    return row


def test_dedup_drops_compile_plain_and_warns(a439_mini):
    # Injeta Compile plain em cima de cada Run.Program (mesmo timestamp) — devem sumir pós-clean.
    rp = a439_mini[a439_mini["EventType"] == "Run.Program"]
    plains = pd.DataFrame([_compile_plain_row(r) for _, r in rp.iterrows()])
    raw = pd.concat([a439_mini, plains], ignore_index=True)

    df, items = clean_event_stream(raw, _A439_CODE_STATES)

    assert set(df["EventType"].unique()).issubset(ALLOWED_EVENTS)
    assert "Compile" not in set(df["EventType"].unique())

    dedup = [i for i in items if i.check == "dedup_compile"]
    assert len(dedup) == 1
    assert dedup[0].severity == "warning"
    assert dedup[0].count == len(plains)


def test_no_dedup_warning_when_no_compile_plain(a439_mini):
    # a439_mini só tem Run.Program/Compile.Error — nada a descartar, nenhum aviso de dedup.
    df, items = clean_event_stream(a439_mini, _A439_CODE_STATES)
    assert set(df["EventType"].unique()).issubset(ALLOWED_EVENTS)
    assert [i for i in items if i.check == "dedup_compile"] == []


def test_correct_binarization_rule(a439_mini):
    # correct = (Run.Program & Score==1.0); Compile.Error é sempre incorreto (D-12).
    df, _ = clean_event_stream(a439_mini, _A439_CODE_STATES)
    expected = ((df["EventType"] == "Run.Program") & (df["Score"] == 1.0)).astype(int)
    assert (df["correct"] == expected).all()

    compile_err = df[df["EventType"] == "Compile.Error"]
    assert (compile_err["correct"] == 0).all()


def test_continuous_score_preserved(a439_mini):
    # Pitfall 4: um Score contínuo (0.5) NÃO pode virar 0/1 na coluna Score.
    raw = a439_mini.copy()
    raw.loc[raw.index[0], "Score"] = 0.5
    df, _ = clean_event_stream(raw, _A439_CODE_STATES)
    assert 0.5 in set(df["Score"].tolist())
