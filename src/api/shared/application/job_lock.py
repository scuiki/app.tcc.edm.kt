"""A trava que garante um único job pesado por vez, vista pelo use case.

`acquire` devolve algo verdadeiro (e usável como context manager, que libera ao sair) quando toma
a trava, ou algo falso quando outro job vivo já a tem. A implementação é a OneJobAtATimeLock.
"""

from __future__ import annotations

from typing import Protocol


class AcquiredJobLock(Protocol):
    def __bool__(self) -> bool: ...

    def __enter__(self) -> "AcquiredJobLock": ...

    def __exit__(self, exc_type, exc, tb) -> bool | None: ...


class JobLock(Protocol):
    def acquire(self, operation: str, job_id: int | None) -> AcquiredJobLock: ...
