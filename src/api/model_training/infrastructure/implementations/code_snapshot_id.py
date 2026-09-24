# CodeSnapshotId, vira nome de arquivo no cache de AST paths.

from __future__ import annotations

import re
from dataclasses import dataclass

# Nome de arquivo do cache, só alfanumérico e . _ -, fechando separador de caminho, NUL e afins.
_CSID_ALLOWED = re.compile(r"[A-Za-z0-9._-]+")


# Validação de admissão (aceita a forma conhecida, recusa o resto) em vez de tentar limpar o valor.
@dataclass(frozen=True)
class CodeSnapshotId:
    value: str

    def __post_init__(self) -> None:
        if ".." in self.value or not _CSID_ALLOWED.fullmatch(self.value):
            raise ValueError(f"CodeStateID inseguro para nome de arquivo: {self.value!r}")

    def __str__(self) -> str:
        return self.value

    def __fspath__(self) -> str:
        return self.value
