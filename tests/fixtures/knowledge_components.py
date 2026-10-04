# Fixtures dos testes de knowledge_components.

from __future__ import annotations

import json

import numpy as np
import pytest

_NAMING_OPENING = "The knowledge components list is: "


def fake_embed(codes: list[str]) -> np.ndarray:
    # Vetores falsos no lugar do CodeBERT e do SBERT, um por texto, sem carregar o modelo
    return np.array([[len(code), sum(map(ord, code)) % 97 + 1, 1.0] for code in codes])


def naming_answer(prompt: str) -> dict | None:
    # Para o pedido de nomeação, a resposta da Tabela 10 com o primeiro KC da lista, e senão None
    if not prompt.startswith(_NAMING_OPENING):
        return None
    names = json.loads(prompt[len(_NAMING_OPENING) :].split("\n", 1)[0])
    return {
        "reasoning": "One KC covers the others.",
        "representative kc": names[0],
        "summary name": None,
    }


@pytest.fixture
def fake_claude_envelope():
    # O JSON que `claude -p --output-format json` devolve, para os testes nunca chamarem o binário
    def build(structured_output, result: str = "") -> dict:
        return {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": result,
            "structured_output": structured_output,
        }

    return build
