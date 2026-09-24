# Interface do LLM que o KCGen-KT usa; `ml/` só declara, quem implementa e injeta é a aplicação.

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system: str, prompt: str, schema: dict) -> dict:
        # Saída do LLM validada por `schema`, que a app mapeia para `claude -p --json-schema`.
        ...
