# ClassroomSlug, o nome da turma normalizado, para comparar nomes com grafias diferentes.

from __future__ import annotations

from api.shared.domain.services.text_to_slug import text_to_slug
from dataclasses import dataclass

_SLUG_FALLBACK = "classroom"


@dataclass(frozen=True)
class ClassroomSlug:
    # "Turma 6" e "turma  6" são a mesma turma; os arquivos dela ficam no id, não no nome

    value: str

    @classmethod
    def from_name(cls, name: str) -> "ClassroomSlug":
        return cls(text_to_slug(name, _SLUG_FALLBACK))

    def __str__(self) -> str:
        return self.value
