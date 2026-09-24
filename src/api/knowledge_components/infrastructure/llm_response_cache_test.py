"""O cache de respostas do LLM: a chave é o hash de tudo que determina a resposta, um acerto não
chama o LLM, e o cache é isolado por problema (gravar um não muda o outro).
"""

from __future__ import annotations

from api.knowledge_components.infrastructure.llm_response_cache import (
    cache_get,
    cache_put,
    kc_input_hash,
)

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
    # gravar o problema "1" NÃO cria entrada para o problema "2" — re-rodar 1 problema
    # não aproveita/invalida o outro indevidamente.
    key1 = kc_input_hash(_MODEL, _PV, "amostras-1")
    cache_put(tmp_path, problem_id="1", key=key1, record={"parsed": {"kcs": [{"name": "a"}]}})

    # O problema 2, com sua própria chave, continua miss.
    key2 = kc_input_hash(_MODEL, _PV, "amostras-2")
    assert cache_get(tmp_path, problem_id="2", key=key2) is None
    # E o problema 1 segue intacto.
    assert cache_get(tmp_path, problem_id="1", key=key1) is not None
