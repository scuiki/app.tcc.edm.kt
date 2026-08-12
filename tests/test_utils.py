"""Testes do util público compartilhado (IN-01): run_program_only.

Slug e progsnap_aid saíram daqui para value objects (test_values.py). O que resta é o recorte
do stream canônico para a stack de modelagem — a fonte única que fecha o training-serving skew."""

from __future__ import annotations

import pandas as pd

from edmkt_app import utils


def _mixed_stream() -> pd.DataFrame:
    # Espelha o Parquet canônico da Fase 3: ALLOWED_EVENTS = {Run.Program, Compile.Error}.
    return pd.DataFrame(
        [
            {"SubjectID": "S1", "EventType": "Run.Program", "correct": 1},
            {"SubjectID": "S1", "EventType": "Compile.Error", "correct": 0},
            {"SubjectID": "S2", "EventType": "Compile.Error", "correct": 0},
            {"SubjectID": "S2", "EventType": "Run.Program", "correct": 0},
        ]
    )


def test_run_program_only_drops_compile_errors():
    out = utils.run_program_only(_mixed_stream())

    assert list(out["EventType"].unique()) == ["Run.Program"]
    assert len(out) == 2


def test_run_program_only_does_not_mutate_the_caller_frame():
    df = _mixed_stream()
    utils.run_program_only(df)

    assert len(df) == 4  # o canônico segue intacto para a EDA, que PRECISA dos Compile.Error


def test_run_program_only_reindexes():
    # build_sequences/split_by_subject iteram por posição em vários pontos; um índice com
    # buracos (herdado do recorte) é fonte de desalinhamento silencioso.
    out = utils.run_program_only(_mixed_stream())

    assert list(out.index) == list(range(len(out)))
