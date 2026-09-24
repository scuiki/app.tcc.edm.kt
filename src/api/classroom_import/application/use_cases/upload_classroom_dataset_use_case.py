# Só grava o estado cru deste upload; a trava de job fica no import, não aqui.

from __future__ import annotations

from pathlib import Path

from api.classrooms.domain.value_objects.classroom_slug import ClassroomSlug
from api.classroom_import.application.dtos.upload_classroom_dataset_dto import (
    UploadClassroomDatasetResponseDTO,
)
from api.classroom_import.domain.interfaces.progsnap_upload_extractor import IProgSnapUploadExtractor


class UploadClassroomDatasetUseCase:
    def __init__(self, extractor: IProgSnapUploadExtractor) -> None:
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
