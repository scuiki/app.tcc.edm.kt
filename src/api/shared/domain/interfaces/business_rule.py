# Regra de negócio, devolve a mensagem de recusa ou None; não pode assumir que outra já passou.
from __future__ import annotations

from typing import Any, Protocol


class IBusinessRule(Protocol):
    def check(self, dto: Any) -> str | None: ...
