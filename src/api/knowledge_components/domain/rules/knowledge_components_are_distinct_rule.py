"""Regra: fundir um KC com ele mesmo não faz sentido; recusa explícita em vez de depender do rollback."""

from __future__ import annotations

from typing import Any


class KnowledgeComponentsAreDistinctRule:
    def check(self, dto: Any) -> str | None:
        if dto.keep_kc_id == dto.drop_kc_id:
            return "keep_kc_id e drop_kc_id são o mesmo KC"
        return None
