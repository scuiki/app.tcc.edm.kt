# Interface do LLM que o KCGen-KT usa; `ml/` só declara, quem implementa e injeta é a aplicação.

from __future__ import annotations

from typing import Callable, Protocol


# Resposta vazia, que não é JSON ou fora do formato pedido, e uma nova chamada pode vir certa
class InvalidLLMResponseError(ValueError):
    pass


class LLMClient(Protocol):
    def generate(
        self,
        system: str,
        prompt: str,
        schema: dict | None = None,
        validate: Callable[[dict], object] | None = None,
    ) -> dict:
        # A resposta em JSON, e com `validate` só sai a que passa nele sem InvalidLLMResponseError
        ...
