"""Forward-only SQL migrations applied over PRAGMA user_version (D-02)."""

from __future__ import annotations

from edmkt_app.persistence.migrations.runner import run_migrations

__all__ = ["run_migrations"]
