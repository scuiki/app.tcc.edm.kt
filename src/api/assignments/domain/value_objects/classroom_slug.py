# ClassroomSlug, a forma segura do nome da turma que vira nome de diretório em data/.

from __future__ import annotations

import re
from dataclasses import dataclass

_SLUG_FALLBACK = "classroom"


@dataclass(frozen=True)
class ClassroomSlug:
    # O slug é a única forma segura do nome que vira caminho; nunca use o nome cru como diretório.

    value: str

    @classmethod
    def from_name(cls, name: str) -> "ClassroomSlug":
        # Idempotente por construção, re-slugificar um slug devolve ele mesmo.
        s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
        return cls(s or _SLUG_FALLBACK)

    def __str__(self) -> str:
        return self.value

    def __fspath__(self) -> str:
        return self.value
