"""call_with_retry: repete só o erro transiente (rede, 429, 5xx), com backoff e um teto de
tentativas; o conteúdo vazio é falha dura e sobe na hora. O sleep do backoff é substituído.
"""

from __future__ import annotations

import pytest

from api.knowledge_components.infrastructure.llm_call_retry import (
    EmptyContentError,
    TransientLLMError,
    call_with_retry,
)


def test_transient_is_retried_then_reraised(monkeypatch):
    # N tentativas que sempre falham transiente → re-levanta TransientLLMError; sleep patchado.
    calls = {"n": 0}

    def _always_transient():
        calls["n"] += 1
        raise TransientLLMError("429")

    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

    with pytest.raises(TransientLLMError):
        call_with_retry(_always_transient, retries=3)

    # Tentou mais de uma vez (retry de fato aconteceu).
    assert calls["n"] >= 2


def test_transient_then_success(monkeypatch):
    # Falha transiente seguida de sucesso → call_with_retry devolve o resultado bom.
    seq = iter([TransientLLMError("5xx"), None])

    def _fn():
        exc = next(seq)
        if exc is not None:
            raise exc
        return {"kcs": [{"name": "ok"}]}

    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

    out = call_with_retry(_fn, retries=3)
    assert out == {"kcs": [{"name": "ok"}]}


def test_retries_below_one_raises_value_error():
    # retries=0 → range(0) vazio, last_exc fica None, e `raise None` daria TypeError opaco.
    # Guard explícito: ValueError claro antes de tentar.
    with pytest.raises(ValueError):
        call_with_retry(lambda: {"kcs": [{"name": "x"}]}, retries=0)


def test_empty_content_is_not_retried(monkeypatch):
    # Conteúdo-vazio NÃO é transiente: re-chamar não ajuda → propaga sem retry inútil.
    calls = {"n": 0}

    def _empty():
        calls["n"] += 1
        raise EmptyContentError("0 KCs")

    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

    with pytest.raises(EmptyContentError):
        call_with_retry(_empty, retries=3)

    assert calls["n"] == 1  # chamado uma única vez, sem retry
