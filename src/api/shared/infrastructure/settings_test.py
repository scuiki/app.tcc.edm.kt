# Uma raiz de dados só para a app layer, definida uma vez só (antes eram SEIS cópias divergentes).
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


# Um único monkeypatch em settings.DATA_ROOT redireciona todo caminho sob data/.
def test_a_single_monkeypatch_redirects_every_path(monkeypatch, tmp_path):
    from api.shared.infrastructure.filesystem import data_layout

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)

    assert tmp_path in data_layout.raw_upload_dir(1, "envio").parents
