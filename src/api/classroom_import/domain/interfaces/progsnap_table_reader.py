# Lê as tabelas do ProgSnap2; a implementação (CSV) fica na infraestrutura.

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd

from api.classroom_import.domain.value_objects.import_report import ImportCheck


class IProgSnapTableReader(Protocol):
    def read_main_table(self, path: Path) -> tuple[pd.DataFrame | None, list[ImportCheck]]:
        # O MainTable com os tipos coagidos, ou None se houver falha fatal, e as checagens.
        ...

    def read_code_snapshots(self, raw_dir: Path) -> dict[str, str]:
        # `{CodeStateID: código Java}`; sem CodeStates no upload, um dict vazio.
        ...
