# Os contratos do import-linter, rodados na suíte para uma violação reprovar o pytest.

from __future__ import annotations

from pathlib import Path

from importlinter.cli import lint_imports

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def test_every_import_contract_is_kept():
    # Sem cache, para não gravar nada no repositório e rodar com qualquer usuário
    assert lint_imports(config_filename=str(PYPROJECT), no_cache=True, no_logo=True) == 0
