"""Uma raiz de dados só para a app layer.

`DATA_ROOT` tinha SEIS definições (eda, features_cache, ingestion/service, kc_pipeline, train,
mastery_service). Cada consumidor carregava a sua, e o fixture de teste do treino precisava
lembrar de apontar DUAS delas para o tmp_path — esquecer uma faria o teste escrever na árvore
`data/` de verdade, em silêncio.

É a mesma duplicação que `_slug` (7 cópias) e o filtro de evento (2) tinham: conhecimento que
existe em vários lugares e diverge.
"""

from __future__ import annotations

import re
from pathlib import Path

from api.shared.infrastructure import settings

_SRC = next(p for p in Path(__file__).resolve().parents if p.name == "src")


def test_data_root_is_defined_exactly_once():
    definicoes = [
        f.relative_to(_SRC)
        for f in _SRC.rglob("*.py")
        if re.search(r"^DATA_ROOT\s*=", f.read_text(encoding="utf-8"), re.M)
    ]

    assert definicoes == [Path("api/shared/infrastructure/settings.py")], (
        f"DATA_ROOT deveria ter uma definição só; encontrei {len(definicoes)}: {definicoes}"
    )


def test_db_path_is_defined_exactly_once():
    definicoes = [
        f.relative_to(_SRC)
        for f in _SRC.rglob("*.py")
        if re.search(r"^DB_PATH\s*=", f.read_text(encoding="utf-8"), re.M)
    ]

    assert definicoes == [Path("api/shared/infrastructure/settings.py")]


def test_a_single_monkeypatch_redirects_every_path(monkeypatch, tmp_path):
    """Um único monkeypatch em settings.DATA_ROOT redireciona todo caminho sob data/.

    Que ninguém guarde a própria cópia da raiz é o que test_data_root_is_defined_exactly_once
    garante; aqui se prova que data_layout lê a raiz em tempo de chamada, não no import.
    """
    from api.shared.infrastructure.filesystem import data_layout

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)

    assert tmp_path in data_layout.cleaned_submissions_path("turma-x", 439).parents
