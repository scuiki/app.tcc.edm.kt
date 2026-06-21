"""RED — cache fino do LLM keyed por hash (KC-04, D-02/D-03).

Pina o cache por-estágio/por-problema: a chave é sha256(model_id + prompt_version + payload)
(determinística); um hit devolve o registro cru cacheado SEM chamar o LLM (contado); e o cache
é isolado por problema — gravar o problema A não muda o lookup do problema B (D-02: re-rodar 1
problema não invalida os outros). O registro guarda a RESPOSTA CRUA + identidade (D-03) — o
objeto científico reproduzível.

Wave 0: `edmkt_app.kc_cache` ainda não existe → FALHA RED (gate da Wave 1).
"""

from __future__ import annotations

# RED: módulo de cache ainda não existe (gate da Wave 1).
from edmkt_app.kc_cache import (  # noqa: E402
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
    # O registro guarda a resposta CRUA + identidade (D-03), recuperável intacto no hit.
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
    assert calls["n"] == 0  # hit ⇒ LLM nunca chamado (T-05-01 DoS / economia de cota)


def test_per_problem_isolation(tmp_path):
    # D-02: gravar o problema "1" NÃO cria entrada para o problema "2" — re-rodar 1 problema
    # não aproveita/invalida o outro indevidamente.
    key1 = kc_input_hash(_MODEL, _PV, "amostras-1")
    cache_put(tmp_path, problem_id="1", key=key1, record={"parsed": {"kcs": [{"name": "a"}]}})

    # O problema 2, com sua própria chave, continua miss.
    key2 = kc_input_hash(_MODEL, _PV, "amostras-2")
    assert cache_get(tmp_path, problem_id="2", key=key2) is None
    # E o problema 1 segue intacto.
    assert cache_get(tmp_path, problem_id="1", key=key1) is not None
