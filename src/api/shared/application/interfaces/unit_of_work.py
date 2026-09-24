# Transação vista pelo use case, tudo dentro do `with` é gravado junto ou nada é.
from __future__ import annotations

from typing import Protocol


# Levantar dentro do `with` desfaz tudo, é assim que uma regra avaliada após a mudança a desfaz.
class IUnitOfWork(Protocol):
    def __enter__(self) -> "IUnitOfWork": ...

    def __exit__(self, exc_type, exc, tb) -> bool | None: ...
