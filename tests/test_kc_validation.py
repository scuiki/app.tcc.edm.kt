"""RED — validação por conteúdo + transiente vs falha-dura (KC-04, D-04).

Pina a regra metodológica do KC-04: a saída do LLM é validada por CONTEÚDO (não por existência
de arquivo). `{}` / `{"kcs": []}` / KC sem `name` = EmptyContentError (falha-dura, re-chamar
não ajuda). Um erro TRANSIENTE (rede/429/5xx/exit≠0, sinalizado por TransientLLMError) é
retentado com backoff até N e então re-levantado. O sleep do backoff é patchado p/ teste rápido.

Wave 0: os alvos (`validate_kc_result`, `call_with_retry`) ainda não existem → FALHA RED.
"""

from __future__ import annotations

import pytest

from edmkt_app.llm.validation import (  # noqa: E402
    EmptyContentError,
    TransientLLMError,
    call_with_retry,
    validate_kc_result,
)


def test_empty_dict_is_hard_fail():
    with pytest.raises(EmptyContentError):
        validate_kc_result({})


def test_missing_kcs_key_is_hard_fail():
    with pytest.raises(EmptyContentError):
        validate_kc_result({"problem_description": "x"})


def test_empty_kcs_list_is_hard_fail():
    # ≥1 KC por problema (KC-04) — 0 KCs é falha-dura, não Q-matrix incompleta.
    with pytest.raises(EmptyContentError):
        validate_kc_result({"kcs": []})


def test_kc_without_name_is_hard_fail():
    with pytest.raises(EmptyContentError):
        validate_kc_result({"kcs": [{"reasoning": "sem nome"}]})


def test_valid_result_passes():
    # Resultado bem-formado não levanta (≥1 KC, cada um com 'name').
    validate_kc_result({"kcs": [{"name": "laços", "reasoning": "usa for"}]})


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
    # WR-03: retries=0 → range(0) vazio, last_exc fica None, e `raise None` daria TypeError opaco.
    # Guard explícito: ValueError claro antes de tentar.
    with pytest.raises(ValueError):
        call_with_retry(lambda: {"kcs": [{"name": "x"}]}, retries=0)


def test_empty_content_is_not_retried(monkeypatch):
    # Conteúdo-vazio NÃO é transiente: re-chamar não ajuda → propaga sem retry inútil (D-04).
    calls = {"n": 0}

    def _empty():
        calls["n"] += 1
        raise EmptyContentError("0 KCs")

    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)

    with pytest.raises(EmptyContentError):
        call_with_retry(_empty, retries=3)

    assert calls["n"] == 1  # chamado uma única vez, sem retry
