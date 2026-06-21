# DIP boundary (D-01, KC-01): the pure core DECLARES the LLM transport contract; the app
# (edmkt_app/llm/claude_cli.py) IMPLEMENTS it. The core never imports anthropic, edmkt_app,
# subprocess, or the filesystem — the transport is injected as an LLMClient.

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system: str, prompt: str, schema: dict) -> dict:
        """Return the structured (schema-validated) LLM output for one call.

        `schema` is the JSON Schema the transport constrains the output to (the app maps it
        to `claude -p --json-schema`); the returned dict is the parsed structured output.
        """
        ...
