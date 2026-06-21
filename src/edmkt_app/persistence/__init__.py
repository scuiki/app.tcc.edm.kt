"""Persistence layer for EDM·KT (SQLite + filesystem, D-03).

Public surface = the DIP boundary the FastAPI app depends inward on. The scientific core
(edmkt_core) is framework-free and NEVER imports from here; this package owns all SQLite
and filesystem I/O.
"""

from __future__ import annotations

from edmkt_app.persistence.db import connect, transaction
from edmkt_app.persistence.migrations.runner import run_migrations

__all__ = ["connect", "transaction", "run_migrations"]
