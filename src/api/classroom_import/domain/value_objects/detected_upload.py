# O que o upload encontrou no zip do professor, o diretório cru e as tabelas do ProgSnap2.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DetectedUpload:
    raw_dir: Path  # onde o zip foi extraído, intocado
    main_tables: list[Path]  # uma ou mais MainTable.csv, o professor escolhe qual importar
    code_snapshots: Path | None  # o CodeStates.csv, se o zip trouxer
