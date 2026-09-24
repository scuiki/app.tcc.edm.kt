# Só grava o estado cru deste envio; a trava de job fica no import, não aqui.

from __future__ import annotations

from pathlib import Path

from api.classroom_import.application.dtos.upload_classroom_dataset_dto import (
    UploadClassroomDatasetResponseDTO,
)
from api.classroom_import.domain.interfaces.progsnap_upload_extractor import IProgSnapUploadExtractor
from api.classrooms.domain.interfaces.classroom_repository import IClassroomRepository
from api.shared.application.services.clock import utc_now_iso
from api.shared.domain.errors.not_found import NotFound
from api.shared.domain.services.text_to_slug import text_to_slug


class UploadClassroomDatasetUseCase:
    def __init__(
        self, classrooms: IClassroomRepository, extractor: IProgSnapUploadExtractor
    ) -> None:
        self._classrooms = classrooms
        self._extractor = extractor

    def execute(
        self, zip_path: Path, classroom_id: int, zip_filename: str
    ) -> UploadClassroomDatasetResponseDTO:
        if self._classrooms.get(classroom_id) is None:
            raise NotFound("turma inexistente")
        # A pasta do envio leva a data e o nome do zip, limpo porque o nome vem do usuário
        sent_at = utc_now_iso()[:19].replace(":", "-")
        upload_name = f"{sent_at}_{text_to_slug(Path(zip_filename).stem, 'envio')}"
        upload = self._extractor.extract(zip_path, classroom_id, upload_name)
        return UploadClassroomDatasetResponseDTO(
            classroom_id=classroom_id,
            raw_dir=str(upload.raw_dir),
            main_tables=[str(p) for p in upload.main_tables],
            code_snapshots=None if upload.code_snapshots is None else str(upload.code_snapshots),
        )
