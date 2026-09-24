from __future__ import annotations

from typing import Protocol


# O web grava a linha do job e dispara o worker sem esperar, o estado vive na linha do job.
class IBackgroundJobLauncher(Protocol):
    def launch(self, assignment_id: int, job_id: int) -> None: ...
