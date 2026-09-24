"""Pacote de transporte LLM (D-01): a ÚNICA porta para a subscription do Claude.

Reexporta o transporte (`call_claude`, `ClaudeCLIClient`), as exceções de classificação
(`TransientLLMError`, `EmptyContentError`) e os helpers de validação/retry. O core puro
(`ml.kc_generation.llm_client.LLMClient`) declara o contrato; este pacote o implementa via o binário
`claude` — o SDK `anthropic` nunca é importado.
"""

from __future__ import annotations

from edmkt_app.llm.claude_cli import DISALLOWED_TOOLS, ClaudeCLIClient, call_claude
from edmkt_app.llm.validation import (
    EmptyContentError,
    TransientLLMError,
    call_with_retry,
    validate_kc_result,
)

__all__ = [
    "DISALLOWED_TOOLS",
    "ClaudeCLIClient",
    "EmptyContentError",
    "TransientLLMError",
    "call_claude",
    "call_with_retry",
    "validate_kc_result",
]
