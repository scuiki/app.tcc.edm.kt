# Os estados de um job em background (treino ou geração de KCs).

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"  # gravado pelo web; o subprocess ainda não começou
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
