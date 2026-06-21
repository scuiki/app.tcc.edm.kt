"""edmkt_app — the FastAPI application layer for EDM·KT (TCC 2).

Depends inward on the pure edmkt_core via DIP (D-01): this layer owns I/O (SQLite,
filesystem, HTTP); the core owns the science. edmkt_core NEVER imports from edmkt_app.
"""

from __future__ import annotations

__all__: list[str] = []
