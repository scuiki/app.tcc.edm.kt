# Abre o zip do professor; a implementação (zip) fica na infraestrutura.

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from api.classrooms.domain.value_objects.classroom_slug import ClassroomSlug

from api.classroom_import.domain.value_objects.detected_upload import DetectedUpload


class IProgSnapUploadExtractor(Protocol):
    def extract(self, zip_path: Path, classroom_slug: ClassroomSlug) -> DetectedUpload: ...
