"""O que a importação precisa de fora: abrir o zip do professor e ler as tabelas do ProgSnap2.

As implementações ficam na infraestrutura (zip, CSV). Aqui só a forma do que elas devolvem.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd

from api.assignments.domain.classroom_slug import ClassroomSlug

from api.classroom_import.domain.import_report import ImportCheck


@dataclass(frozen=True)
class DetectedUpload:
    raw_dir: Path  # onde o zip foi extraído, intocado
    main_tables: list[Path]  # uma ou mais MainTable.csv: o professor escolhe qual importar
    code_snapshots: Path | None  # o CodeStates.csv, se o zip trouxer


class ProgSnapUploadExtractor(Protocol):
    def extract(self, zip_path: Path, classroom_slug: ClassroomSlug) -> DetectedUpload: ...


class ProgSnapTableReader(Protocol):
    def read_main_table(self, path: Path) -> tuple[pd.DataFrame | None, list[ImportCheck]]:
        """O MainTable com os tipos coagidos, ou None se houver falha fatal; e as checagens."""
        ...

    def read_code_snapshots(self, raw_dir: Path) -> dict[str, str]:
        """{CodeStateID: código Java}. Sem CodeStates no upload, um dict vazio."""
        ...
