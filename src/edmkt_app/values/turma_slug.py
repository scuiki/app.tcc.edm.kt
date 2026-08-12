"""Componente de diretório derivado do nome de turma que o professor digitou."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SLUG_FALLBACK = "turma"


@dataclass(frozen=True)
class TurmaSlug:
    """Componente de diretório derivado do nome de turma que o professor digitou.

    O nome é entrada arbitrária; o slug é a ÚNICA forma dele que vira caminho. Nunca usar o
    nome cru como diretório (T-03-15).
    """

    value: str

    @classmethod
    def from_name(cls, name: str) -> "TurmaSlug":
        # Idempotente por construção: "-" também cai no [^a-z0-9], então re-slugificar um slug
        # devolve ele mesmo — aplicar duas vezes por engano não corrompe o caminho.
        s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
        return cls(s or _SLUG_FALLBACK)

    def __str__(self) -> str:
        return self.value

    def __fspath__(self) -> str:
        return self.value
