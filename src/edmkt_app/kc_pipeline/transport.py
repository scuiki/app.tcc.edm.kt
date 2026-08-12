"""Transporte LLM do KC-gen: a porta única para o `claude`, com cache e retry.

`_llm_generate` é o seam que os testes monkeypatcham — nenhum teste cruza para o binário real
(T-05-01).
"""

from __future__ import annotations

from pathlib import Path

from edmkt_app.kc_cache import PROMPT_VERSION, cache_get, cache_put, kc_input_hash
from edmkt_app.kc_pipeline import settings
from edmkt_app.llm.claude_cli import ClaudeCLIClient
from edmkt_app.llm.validation import call_with_retry
from edmkt_app.values import ProgSnapAssignmentId, TurmaSlug


def _llm_generate(system: str, prompt: str, schema: dict) -> dict:
    """Porta única para o `claude` (D-01): chamada single-shot text→JSON pelo transporte CLI.

    É o seam que a orquestração injeta como LLMClient e que os testes monkeypatcham — nenhum
    teste cruza para o binário real (T-05-01). cwd neutro corta o contexto CLAUDE.md (Pitfall 1)."""
    return ClaudeCLIClient(model=settings.MODEL_ID).generate(system, prompt, schema)


class _CachedLLM:
    """Adapter LLMClient (DIP) com cache fino + retry, por-problema/por-cluster (D-02/D-04).

    Cada `generate` deriva uma chave de hash do (model, prompt_version, payload) e consulta o
    cache de FS antes de chamar; um hit pula a chamada inteiramente. As chamadas ao `claude`
    passam pelo `_llm_generate` resolvido em runtime (`globals()[...]`) para que o monkeypatch
    de teste sobre o módulo tenha efeito. call_with_retry só repete erro transiente (D-04)."""

    def __init__(self, cache_dir: Path, stage: str) -> None:
        self._cache_dir = cache_dir
        self._stage = stage

    def generate(self, system: str, prompt: str, schema: dict) -> dict:
        key = kc_input_hash(settings.MODEL_ID, PROMPT_VERSION, prompt, system=system, schema=schema)
        cache_id = f"{self._stage}:{key}"
        cached = cache_get(self._cache_dir, problem_id=cache_id, key=key)
        if cached is not None:
            return cached["parsed"]

        # Migração-por-leitura das entradas gravadas antes de system/schema entrarem na chave:
        # elas foram geradas com ESTE mesmo system/schema (o prompt não mudou desde então), então
        # reaproveitá-las é correto e evita re-gastar cota da assinatura. Remover quando não
        # houver mais cache antigo em disco.
        legacy_key = kc_input_hash(settings.MODEL_ID, PROMPT_VERSION, prompt)
        legacy = cache_get(self._cache_dir, problem_id=f"{self._stage}:{legacy_key}", key=legacy_key)
        if legacy is not None:
            cache_put(
                self._cache_dir,
                problem_id=cache_id,
                key=key,
                record={"model_id": settings.MODEL_ID, "prompt_version": PROMPT_VERSION, "parsed": legacy["parsed"]},
            )
            return legacy["parsed"]

        # Resolve _llm_generate no módulo em tempo de chamada — o teste o monkeypatcha (raising
        # False), e um default ligado em def-time ignoraria o patch.
        fn = globals()["_llm_generate"]
        parsed = call_with_retry(lambda: fn(system, prompt, schema))

        cache_put(
            self._cache_dir,
            problem_id=cache_id,
            key=key,
            record={"model_id": settings.MODEL_ID, "prompt_version": PROMPT_VERSION, "parsed": parsed},
        )
        return parsed


def _kc_cache_dir(turma_slug: TurmaSlug, progsnap_aid: ProgSnapAssignmentId) -> Path:
    # Diretório de cache derivado do slug interno + aid (nunca input de usuário) — sem traversal
    # (KC-04). Espelha data/<slug>/kc/ dos artefatos do TCC.
    return settings.DATA_ROOT / turma_slug / "kc" / f"assignment_{progsnap_aid}"
