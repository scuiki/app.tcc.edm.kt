"""Uma transação vista pelo use case: tudo dentro do `with` é gravado junto, ou nada é.

O use case não sabe que é SQLite. Levantar dentro do `with` desfaz tudo; é assim que uma regra
avaliada DEPOIS da mudança (ex.: "nenhum problema ficou sem KC") consegue desfazer a mudança.
"""

from __future__ import annotations

from typing import Protocol


class UnitOfWork(Protocol):
    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc, tb) -> bool | None: ...
