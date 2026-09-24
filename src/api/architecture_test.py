"""As convenções de pasta e de nome de docs/ARCHITECTURE.md, verificadas.

O import-linter garante quem importa quem; este teste garante onde cada coisa mora: o papel de um
arquivo decide a subpasta, e todo Protocol é uma interface com prefixo I. Lê o código com `ast`,
sem importar nada, então não depende de banco, GPU nem do estado de nenhum módulo.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

API = Path(__file__).parent
FEATURES = sorted(p for p in API.iterdir() if p.is_dir() and (p / "__init__.py").exists())
LAYERS = ("domain", "application", "infrastructure", "presentation")

ALLOWED_SUBFOLDERS = {
    "domain": {"entities", "value_objects", "interfaces", "rules", "services"},
    "application": {"use_cases", "dtos", "interfaces", "services"},
    "infrastructure": {"repositories", "implementations"},
    "presentation": {"controllers", "workers"},
}
# O shared/ não é uma funcionalidade: tem pastas de tecnologia e os erros (ver ARCHITECTURE).
SHARED_EXTRA_SUBFOLDERS = {
    "domain": {"errors"},
    "infrastructure": {"database", "filesystem"},
    "presentation": {"http"},
}
ALLOWED_ROOT_FILES = {
    "presentation": {"dependencies.py"},  # o composition root de cada funcionalidade
}
SHARED_EXTRA_ROOT_FILES = {"infrastructure": {"settings.py"}}

# O sufixo do arquivo diz o papel; o papel diz a subpasta.
SUFFIX_TO_SUBFOLDER = {
    "_entity": "entities",
    "_rule": "rules",
    "_use_case": "use_cases",
    "_dto": "dtos",
    "_controller": "controllers",
    "_worker": "workers",
}


def _python_files():
    for f in API.rglob("*.py"):
        if "__pycache__" not in f.parts:
            yield f


def _layer_and_subfolder(path: Path) -> tuple[str | None, str | None]:
    """('domain', 'entities') para api/<feature>/domain/entities/x.py; (None, None) fora das camadas."""
    parts = path.relative_to(API).parts
    if len(parts) < 3 or parts[1] not in LAYERS:
        return None, None
    return parts[1], (parts[2] if len(parts) > 3 else None)


def _protocols(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and any(isinstance(b, ast.Name) and b.id == "Protocol" for b in node.bases)
    ]


@pytest.mark.parametrize("feature", FEATURES, ids=lambda p: p.name)
def test_each_layer_holds_only_its_role_subfolders(feature):
    is_shared = feature.name == "shared"
    for layer in LAYERS:
        layer_dir = feature / layer
        assert layer_dir.is_dir(), f"{feature.name} sem a camada {layer}/"
        allowed = ALLOWED_SUBFOLDERS[layer] | (SHARED_EXTRA_SUBFOLDERS.get(layer, set()) if is_shared else set())
        subfolders = {p.name for p in layer_dir.iterdir() if p.is_dir() and p.name != "__pycache__"}
        assert subfolders <= allowed, f"{feature.name}/{layer}/: subpasta fora do padrão {subfolders - allowed}"

        root_files = {p.name for p in layer_dir.glob("*.py")} - {"__init__.py"}
        allowed_files = ALLOWED_ROOT_FILES.get(layer, set()) | (
            SHARED_EXTRA_ROOT_FILES.get(layer, set()) if is_shared else set()
        )
        # O teste de um arquivo permitido na raiz também é permitido.
        allowed_files |= {f.removesuffix(".py") + "_test.py" for f in allowed_files}
        loose = root_files - allowed_files
        assert not loose, f"{feature.name}/{layer}/: arquivos soltos na raiz da camada {sorted(loose)}"


def test_a_role_suffix_lives_in_its_subfolder():
    wrong = []
    for f in _python_files():
        layer, subfolder = _layer_and_subfolder(f)
        # Em interfaces/, o sufixo nomeia o contrato definido (business_rule.py é IBusinessRule).
        if layer is None or subfolder == "interfaces":
            continue
        stem = f.stem.removesuffix("_test")
        for suffix, expected in SUFFIX_TO_SUBFOLDER.items():
            if stem.endswith(suffix) and subfolder != expected:
                wrong.append(f"{f.relative_to(API)} deveria estar em {expected}/")
        if stem.startswith("sqlite_") and stem.endswith("_repository") and subfolder != "repositories":
            wrong.append(f"{f.relative_to(API)} deveria estar em repositories/")
    assert not wrong, "\n".join(wrong)


def test_every_protocol_is_an_interface_named_with_i():
    wrong = []
    for f in _python_files():
        if f.stem.endswith("_test"):
            continue
        for name in _protocols(f):
            public = name.lstrip("_")
            if not (public.startswith("I") and public[1:2].isupper()):
                wrong.append(f"{f.relative_to(API)}: {name} deveria começar com I")
            # Um Protocol privado (_IAlgo) é detalhe de tipagem do único arquivo que o usa e pode
            # morar ao lado dele. Os públicos são contratos entre camadas: moram em interfaces/.
            if not name.startswith("_") and "interfaces" not in f.parts:
                wrong.append(f"{f.relative_to(API)}: {name} deveria estar em interfaces/")
    assert not wrong, "\n".join(wrong)
