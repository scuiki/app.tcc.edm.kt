# O composition root da extração de KCs, com o cliente real do `claude` quando não há um falso.

from __future__ import annotations

from api.knowledge_components.presentation import dependencies


def test_the_extraction_calls_the_haiku_by_default(tmp_db, monkeypatch):
    built: list[dict] = []
    monkeypatch.setattr(
        dependencies, "ClaudeCliLLMClient", lambda **kwargs: built.append(kwargs) or object()
    )

    dependencies.build_run_kc_generation_use_case(tmp_db)

    assert built == [{"model": "claude-haiku-4-5-20251001"}]
