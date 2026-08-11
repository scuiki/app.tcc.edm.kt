"""Testes do util público compartilhado (IN-01): progsnap_aid + slug + run_program_only.

Pinam o contrato extraído de train/mastery_service/eda para um único módulo público, de modo
que call sites fora do módulo dono (ex.: api/dashboard.py) não cruzem a fronteira do underscore.
"""

from __future__ import annotations

import pandas as pd
import pytest

from edmkt_app import utils


def test_progsnap_aid_extracts_numeric_suffix():
    assert utils.progsnap_aid("Assignment 439") == 439
    assert utils.progsnap_aid("A439") == 439
    assert utils.progsnap_aid("439") == 439


def test_progsnap_aid_raises_without_digits():
    with pytest.raises(ValueError, match="não derivável"):
        utils.progsnap_aid("sem numero")


def test_slug_normalizes_and_falls_back():
    assert utils.slug("Turma 6") == "turma-6"
    assert utils.slug("  ") == "turma"  # vazio → fallback determinístico


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


def test_dashboard_uses_public_util_not_private_crossmodule():
    # IN-01: api/dashboard.py deriva o progsnap_id pelo util PÚBLICO, não pelo _progsnap_aid
    # privado de mastery_service. Provamos que é o util público que é chamado.
    from edmkt_app.api import dashboard

    assert dashboard.utils.progsnap_aid is utils.progsnap_aid
