# Fixtures dos testes de knowledge_components.

from __future__ import annotations

import pytest


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
