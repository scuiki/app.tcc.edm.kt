"""CodeStateID do ProgSnap2 — o único identificador do dataset que vira nome de arquivo."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Nome de arquivo do cache de paths: alfanumérico + . _ - e nada mais. Fecha separador de
# caminho, NUL e qualquer coisa que o FS interprete.
_CSID_ALLOWED = re.compile(r"[A-Za-z0-9._-]+")


@dataclass(frozen=True)
class CodeStateId:
    """CodeStateID do ProgSnap2 que vira NOME DE ARQUIVO no cache de features.

    Único ponto do projeto em que um identificador vindo do dataset do professor é usado como
    caminho, então a validação é de admissão: aceita a forma conhecida e rejeita todo o resto,
    em vez de tentar limpar (T-04-CSID).
    """

    value: str

    def __post_init__(self) -> None:
        if ".." in self.value or not _CSID_ALLOWED.fullmatch(self.value):
            raise ValueError(f"CodeStateID inseguro para nome de arquivo: {self.value!r}")

    def __str__(self) -> str:
        return self.value

    def __fspath__(self) -> str:
        return self.value
