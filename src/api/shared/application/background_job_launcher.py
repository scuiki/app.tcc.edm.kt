"""Disparar um job pesado em background, visto pelo use case.

O web grava a linha do job e dispara o worker sem esperar; o estado vive na linha do job. A
implementação (subprocess) fica na infraestrutura.
"""

from __future__ import annotations

from typing import Protocol


class BackgroundJobLauncher(Protocol):
    def launch(self, assignment_id: int, job_id: int) -> None: ...
