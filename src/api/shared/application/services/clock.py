# O relógio da aplicação, todo timestamp gravado no banco sai daqui, em UTC e ISO 8601.

from __future__ import annotations

from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
