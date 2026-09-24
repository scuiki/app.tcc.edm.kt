"""Onde o dado limpo mora: um Parquet por assignment. A implementação fica na infraestrutura.

Gravar é em dois tempos, porque o disco não participa da transação do banco: `stage` escreve os
arquivos temporários, e só depois do COMMIT o use case chama `publish`. Se a transação falhar, o
use case chama `discard`, e o dado anterior (se havia) continua intacto.
"""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId


class StagedCleanedSubmissions(Protocol):
    def publish(self) -> None: ...

    def discard(self) -> None: ...


class CleanedSubmissionsStore(Protocol):
    def stage(self, classroom_slug: ClassroomSlug, cleaned: pd.DataFrame) -> StagedCleanedSubmissions: ...

    def read(self, classroom_slug: ClassroomSlug, progsnap_assignment_id: ProgSnapAssignmentId) -> pd.DataFrame: ...

    def exists(self, classroom_slug: ClassroomSlug, progsnap_assignment_id: ProgSnapAssignmentId) -> bool: ...
