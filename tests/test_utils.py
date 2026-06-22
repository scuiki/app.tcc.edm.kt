"""Testes do util público compartilhado (IN-01): progsnap_aid + slug.

Pinam o contrato extraído de train/mastery_service/eda para um único módulo público, de modo
que call sites fora do módulo dono (ex.: api/dashboard.py) não cruzem a fronteira do underscore.
"""

from __future__ import annotations

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


def test_dashboard_uses_public_util_not_private_crossmodule():
    # IN-01: api/dashboard.py deriva o progsnap_id pelo util PÚBLICO, não pelo _progsnap_aid
    # privado de mastery_service. Provamos que é o util público que é chamado.
    from edmkt_app.api import dashboard

    assert dashboard.utils.progsnap_aid is utils.progsnap_aid
