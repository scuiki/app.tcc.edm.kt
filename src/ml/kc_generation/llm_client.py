"""A interface do LLM que o KCGen-KT usa. O `ml/` declara; a aplicação implementa.

O `ml/` nunca importa o SDK, a aplicação, subprocess nem disco: o transporte chega injetado.
"""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system: str, prompt: str, schema: dict) -> dict:
        """Return the structured (schema-validated) LLM output for one call.

        `schema` is the JSON Schema the transport constrains the output to (the app maps it
        to `claude -p --json-schema`); the returned dict is the parsed structured output.
        """
        ...
