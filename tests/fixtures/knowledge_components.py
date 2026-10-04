# Fixtures dos testes de knowledge_components.

from __future__ import annotations

import numpy as np
import pytest


def fake_embed(codes: list[str]) -> np.ndarray:
    # Vetores falsos no lugar do CodeBERT, um por código, sem carregar o modelo
    return np.array([[len(code), sum(map(ord, code)) % 97 + 1, 1.0] for code in codes])


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
