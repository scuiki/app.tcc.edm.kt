"""Testes do util público compartilhado (IN-01): keep_only_program_runs.

Slug e progsnap_aid saíram daqui para value objects (test_values.py). O que resta é o recorte
do stream canônico para a stack de modelagem — a fonte única que fecha o training-serving skew."""

from __future__ import annotations

import pandas as pd

from api.classroom_import.domain.services import submission_event


def _mixed_stream() -> pd.DataFrame:
    # Espelha o Parquet canônico da Fase 3: ALLOWED_EVENTS = {Run.Program, Compile.Error}.
    return pd.DataFrame(
        [
            {"student_id": "S1", "event_type": "Run.Program", "is_correct": 1},
            {"student_id": "S1", "event_type": "Compile.Error", "is_correct": 0},
            {"student_id": "S2", "event_type": "Compile.Error", "is_correct": 0},
            {"student_id": "S2", "event_type": "Run.Program", "is_correct": 0},
        ]
    )


def test_run_program_only_drops_compile_errors():
    out = submission_event.keep_only_program_runs(_mixed_stream())

    assert list(out["event_type"].unique()) == ["Run.Program"]
    assert len(out) == 2


def test_run_program_only_does_not_mutate_the_caller_frame():
    df = _mixed_stream()
    submission_event.keep_only_program_runs(df)

    assert len(df) == 4  # o canônico segue intacto para a EDA, que PRECISA dos Compile.Error


def test_run_program_only_reindexes():
    # build_student_sequences/split_students_into_train_and_test iteram por posição em vários pontos; um índice com
    # buracos (herdado do recorte) é fonte de desalinhamento silencioso.
    out = submission_event.keep_only_program_runs(_mixed_stream())

    assert list(out.index) == list(range(len(out)))
