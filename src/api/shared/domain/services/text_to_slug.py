# Um texto na forma segura para comparar ou virar caminho, só minúsculas, números e hífen.

from __future__ import annotations

import re


def text_to_slug(text: str, fallback: str) -> str:
    # Idempotente, e um texto sem nenhum caractere aproveitável vira o `fallback`
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-") or fallback
