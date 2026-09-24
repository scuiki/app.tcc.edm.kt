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


def test_every_consumer_reads_the_shared_root(monkeypatch, tmp_path):
    """Um único monkeypatch tem de redirecionar TODOS os consumidores.

    Enquanto cada módulo tinha a sua cópia, redirecionar um não redirecionava os outros — e
    nada avisava. Este teste é a rede: se alguém reintroduzir uma cópia local, ele quebra.
    """
    from edmkt_app import eda, features_cache
    from edmkt_app.ingestion import service
    from edmkt_app.kc_pipeline import transport
    from edmkt_app.train import stages

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)

    for modulo in (eda, features_cache, service, transport, stages):
        assert not hasattr(modulo, "DATA_ROOT"), (
            f"{modulo.__name__} voltou a ter a própria DATA_ROOT"
        )

    # E o caminho derivado de fato aponta para o tmp — não é só ausência de atributo.
    from api.shared.infrastructure import data_layout
    from edmkt_app.values import ProgSnapAssignmentId, TurmaSlug

    path = data_layout.cleaned_submissions_path(TurmaSlug("turma-x"), ProgSnapAssignmentId(439))
    assert tmp_path in path.parents
