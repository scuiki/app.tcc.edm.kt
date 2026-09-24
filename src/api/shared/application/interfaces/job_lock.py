# `acquire` devolve algo truthy (e usável como context manager) quando toma a trava, ou falso.
from __future__ import annotations

from typing import Protocol


class IAcquiredJobLock(Protocol):
    def __bool__(self) -> bool: ...

    def __enter__(self) -> "IAcquiredJobLock": ...

    def __exit__(self, exc_type, exc, tb) -> bool | None: ...


class IJobLock(Protocol):
    def acquire(self, operation: str, job_id: int | None) -> IAcquiredJobLock: ...

    # Pré-check barato e não autoritativo, o gate real é o `acquire` dentro do próprio job.
    def is_another_job_running(self) -> bool:
        ...
