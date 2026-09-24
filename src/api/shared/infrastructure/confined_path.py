"""Caminho provado como estando sob uma raiz — a guarda resolve-depois-confere."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConfinedPath:
    """Caminho provado como estando sob `root`, pela disciplina resolve-depois-confere.

    Confere o caminho JÁ resolvido, não a string: `..` e symlink são fechados antes da
    comparação, e um `..` que volta para dentro segue legítimo. Construir este tipo É a prova —
    quem recebe um `ConfinedPath` não precisa reconferir.
    """

    path: Path
    root: Path

    def __post_init__(self) -> None:
        resolved_root = Path(self.root).resolve()
        resolved = Path(self.path).resolve()
        if resolved != resolved_root and resolved_root not in resolved.parents:
            raise ValueError(f"caminho fora da raiz permitida: {resolved} não está sob {resolved_root}")

    def __fspath__(self) -> str:
        return str(Path(self.path).resolve())

    def __str__(self) -> str:
        return self.__fspath__()
