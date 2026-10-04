# Chave é o hash de tudo que determina a resposta, um acerto não chama o LLM, isolado por problema.
from __future__ import annotations

import json
import threading

import pytest

from api.knowledge_components.infrastructure.implementations.kc_generation_model import (
    KC_GENERATION_MODEL_ID,
    PROMPT_VERSION,
)
from api.knowledge_components.infrastructure.implementations.llm_response_cache import (
    CachedLLMClient,
    cache_get,
    cache_put,
    kc_input_hash,
)
from ml.kc_generation.llm_client import InvalidLLMResponseError

_MODEL = "claude-haiku-4-5-20251001"
_PV = "kcgen-v1"


def test_hash_is_deterministic():
    a = kc_input_hash(_MODEL, _PV, "amostras-do-problema-1")
    b = kc_input_hash(_MODEL, _PV, "amostras-do-problema-1")
    assert a == b
    assert isinstance(a, str) and len(a) == 64  # sha256 hexdigest


def test_hash_changes_with_any_part():
    base = kc_input_hash(_MODEL, _PV, "p1")
    assert kc_input_hash("outro-modelo", _PV, "p1") != base
    assert kc_input_hash(_MODEL, "kcgen-v2", "p1") != base
    assert kc_input_hash(_MODEL, _PV, "p2") != base


def test_miss_returns_none(tmp_path):
    # Cache vazio → miss (None), o caller então chama o LLM.
    assert cache_get(tmp_path, problem_id="1", key="deadbeef") is None


def test_put_then_get_roundtrips_raw_record(tmp_path):
    # O registro guarda a resposta CRUA + identidade, recuperável intacto no hit.
    key = kc_input_hash(_MODEL, _PV, "amostras-1")
    record = {
        "model_id": _MODEL,
        "prompt_version": _PV,
        "input_hash": key,
        "raw_response": '{"kcs": [{"name": "laços"}]}',
        "parsed": {"kcs": [{"name": "laços"}]},
    }
    cache_put(tmp_path, problem_id="1", key=key, record=record)

    got = cache_get(tmp_path, problem_id="1", key=key)
    assert got is not None
    assert got["raw_response"] == record["raw_response"]
    assert got["parsed"] == record["parsed"]
    assert got["model_id"] == _MODEL


def test_hit_does_not_call_llm(tmp_path):
    # Com um hit, o caller NÃO deve invocar o LLM (contado). Simula o padrão get-or-call.
    calls = {"n": 0}
    key = kc_input_hash(_MODEL, _PV, "amostras-1")
    cache_put(tmp_path, problem_id="1", key=key, record={"parsed": {"kcs": [{"name": "x"}]}})

    def _llm():
        calls["n"] += 1
        return {"kcs": [{"name": "fresh"}]}

    cached = cache_get(tmp_path, problem_id="1", key=key)
    result = cached["parsed"] if cached is not None else _llm()

    assert result == {"kcs": [{"name": "x"}]}
    assert calls["n"] == 0  # hit ⇒ LLM nunca chamado


def test_per_problem_isolation(tmp_path):
    # Gravar o problema 1 não cria entrada pro 2, re-rodar um problema não invalida o outro.
    key1 = kc_input_hash(_MODEL, _PV, "amostras-1")
    cache_put(tmp_path, problem_id="1", key=key1, record={"parsed": {"kcs": [{"name": "a"}]}})

    # O problema 2, com sua própria chave, continua miss.
    key2 = kc_input_hash(_MODEL, _PV, "amostras-2")
    assert cache_get(tmp_path, problem_id="2", key=key2) is None
    # E o problema 1 segue intacto.
    assert cache_get(tmp_path, problem_id="1", key=key1) is not None


def test_parallel_writes_keep_every_answer(tmp_path):
    # As chamadas ao LLM rodam em paralelo, e cada uma grava a sua resposta no mesmo arquivo
    def write(i: int) -> None:
        cache_put(tmp_path, problem_id=f"p{i}", key=f"k{i}", record={"parsed": {"i": i}})

    threads = [threading.Thread(target=write, args=(i,)) for i in range(32)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for i in range(32):
        assert cache_get(tmp_path, problem_id=f"p{i}", key=f"k{i}")["parsed"] == {"i": i}


class _ScriptedLLM:
    # Devolve as respostas na ordem dada e conta as chamadas
    def __init__(self, *answers: dict) -> None:
        self._answers = list(answers)
        self.calls = 0

    def generate(self, system, prompt, schema=None, validate=None) -> dict:
        self.calls += 1
        return self._answers.pop(0)


def _require_name(response: dict) -> None:
    if "name" not in response:
        raise InvalidLLMResponseError("sem nome")


def test_an_invalid_response_is_asked_again_and_only_the_valid_one_is_cached(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    llm = _ScriptedLLM({"nome": "laço"}, {"name": "laço"})
    cached = CachedLLMClient(llm, tmp_path, stage="generate")

    first = cached.generate("s", "p", validate=_require_name)
    again = cached.generate("s", "p", validate=_require_name)

    assert first == again == {"name": "laço"}
    assert llm.calls == 2
    stored = json.loads((tmp_path / "kc_cache.json").read_text())
    assert [record["parsed"] for record in stored.values()] == [{"name": "laço"}]


def test_three_invalid_responses_stop_with_nothing_cached(tmp_path, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    llm = _ScriptedLLM({}, {}, {}, {"name": "laço"})
    cached = CachedLLMClient(llm, tmp_path, stage="generate")

    with pytest.raises(InvalidLLMResponseError):
        cached.generate("s", "p", validate=_require_name)

    assert llm.calls == 3
    assert not (tmp_path / "kc_cache.json").exists()


def test_a_cache_hit_keeps_the_order_of_the_kcs_of_the_answer(tmp_path):
    # A ordem das chaves é a dos KCs, e como texto o KC 10 viria antes do KC 2
    answer = {f"KC {i}": {"reasoning": f"r{i}", "name": f"n{i}"} for i in range(1, 13)}
    llm = _ScriptedLLM(answer)
    cached = CachedLLMClient(llm, tmp_path, stage="generate")

    fresh = cached.generate("s", "p")
    replay = cached.generate("s", "p")

    assert llm.calls == 1
    assert list(replay) == list(fresh) == [f"KC {i}" for i in range(1, 13)]


def test_the_cache_key_has_the_model_the_prompt_version_the_system_and_the_schema(tmp_path):
    schema = {"type": "object"}
    CachedLLMClient(_ScriptedLLM({"name": "laço"}), tmp_path, stage="generate").generate(
        "sys", "prompt", schema
    )

    key = kc_input_hash(KC_GENERATION_MODEL_ID, PROMPT_VERSION, "prompt", system="sys", schema=schema)
    assert list(json.loads((tmp_path / "kc_cache.json").read_text())) == [f"generate:{key}"]


def test_a_cached_response_the_validation_refuses_is_asked_again_and_replaced(tmp_path):
    key = kc_input_hash(KC_GENERATION_MODEL_ID, PROMPT_VERSION, "p", system="s")
    cache_put(tmp_path, problem_id=f"generate:{key}", key=key, record={"parsed": {"nome": "x"}})
    llm = _ScriptedLLM({"name": "laço"})
    cached = CachedLLMClient(llm, tmp_path, stage="generate")

    assert cached.generate("s", "p", validate=_require_name) == {"name": "laço"}
    assert cached.generate("s", "p", validate=_require_name) == {"name": "laço"}
    assert llm.calls == 1
