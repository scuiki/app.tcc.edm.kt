"""Recebe o .zip do professor: extrai em data/<turma>/raw/ e lista as MainTable encontradas.

Só escreve o estado privado deste upload (o cru, intocado) e NÃO pega a trava de job: prendê-la
aqui a manteria presa enquanto o professor escolhe qual MainTable importar.
"""

from __future__ import annotations

from pathlib import Path

from api.assignments.domain.classroom_slug import ClassroomSlug
from api.classroom_import.application.upload_classroom_dataset_dto import (
    UploadClassroomDatasetResponseDTO,
)
from api.classroom_import.domain.progsnap_upload import ProgSnapUploadExtractor


class UploadClassroomDatasetUseCase:
    def __init__(self, extractor: ProgSnapUploadExtractor) -> None:
        self._extractor = extractor

    def execute(self, zip_path: Path, classroom_name: str) -> UploadClassroomDatasetResponseDTO:
        slug = ClassroomSlug.from_name(classroom_name)
        upload = self._extractor.extract(zip_path, slug)
        return UploadClassroomDatasetResponseDTO(
            classroom_slug=str(slug),
            raw_dir=str(upload.raw_dir),
            main_tables=[str(p) for p in upload.main_tables],
            code_snapshots=None if upload.code_snapshots is None else str(upload.code_snapshots),
        )
