# call_with_retry repete o erro transiente e a resposta inválida, com backoff e teto.
from __future__ import annotations

import pytest

from api.knowledge_components.infrastructure.implementations.llm_call_retry import (
    TransientLLMError,
    call_with_retry,
)
from ml.kc_generation.llm_client import InvalidLLMResponseError


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
    # retries=0 daria range(0) vazio e `raise None` (TypeError opaco), guard dá ValueError claro.
    with pytest.raises(ValueError):
        call_with_retry(lambda: {"kcs": [{"name": "x"}]}, retries=0)


def test_an_invalid_response_is_asked_three_times_in_all(monkeypatch):
    # A temperatura não é fixável, então uma chamada nova pode vir no formato certo
    calls = {"n": 0}

    def _invalid():
        calls["n"] += 1
        raise InvalidLLMResponseError("0 KCs")

    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

    with pytest.raises(InvalidLLMResponseError):
        call_with_retry(_invalid, retries=3)

    assert calls["n"] == 3


def test_an_invalid_response_then_a_valid_one(monkeypatch):
    seq = iter([InvalidLLMResponseError("sem nome"), None])

    def _fn():
        exc = next(seq)
        if exc is not None:
            raise exc
        return {"KC 1": {"reasoning": "x", "name": "ok"}}

    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

    assert call_with_retry(_fn, retries=3) == {"KC 1": {"reasoning": "x", "name": "ok"}}


def test_any_other_error_is_not_asked_again():
    calls = {"n": 0}

    def _bug():
        calls["n"] += 1
        raise KeyError("name")

    with pytest.raises(KeyError):
        call_with_retry(_bug, retries=3)

    assert calls["n"] == 1
