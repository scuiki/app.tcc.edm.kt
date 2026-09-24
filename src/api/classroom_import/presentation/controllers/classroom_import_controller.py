# HTTP puro sobre os use cases; upload e process em dois passos, zip traz várias MainTable.

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.classroom_import.application.dtos.import_classroom_dataset_dto import (
    ImportClassroomDatasetDTO,
    ImportClassroomDatasetResponseDTO,
)
from api.classroom_import.application.use_cases.import_classroom_dataset_use_case import (
    ImportClassroomDatasetUseCase,
)
from api.classroom_import.application.dtos.upload_classroom_dataset_dto import (
    UploadClassroomDatasetResponseDTO,
)
from api.classroom_import.application.use_cases.upload_classroom_dataset_use_case import (
    UploadClassroomDatasetUseCase,
)
from api.classroom_import.presentation.dependencies import (
    import_classroom_dataset_use_case,
    upload_classroom_dataset_use_case,
)
from api.shared.infrastructure import settings
from api.shared.infrastructure.filesystem.confined_path import ConfinedPath

router = APIRouter(tags=["classroom_import"])

# Teto de bytes do upload contra DoS; o zip-bomb descomprimido tem teto próprio no extrator.
MAX_UPLOAD_BYTES = 512 * 1024 * 1024  # 512 MiB
_UPLOAD_CHUNK = 1024 * 1024


def _save_upload(upload: UploadFile, destination: Path) -> None:
    # Em blocos, contando bytes reais; ler tudo na RAM derrubaria o processo num upload grande.
    written = 0
    with open(destination, "wb") as out:
        while chunk := upload.file.read(_UPLOAD_CHUNK):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                out.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="upload excede o teto de tamanho")
            out.write(chunk)


def _confine(path: Path) -> Path:
    # ConfinedPath prova o confinamento; sem ele, main_table=/etc/passwd leria arquivo arbitrário.
    try:
        return Path(ConfinedPath(path, root=settings.DATA_ROOT))
    except ValueError:
        raise HTTPException(status_code=400, detail="caminho fora da raiz de dados") from None


@router.post("/classroom-imports", response_model=UploadClassroomDatasetResponseDTO)
def upload_classroom_dataset(
    classroom_name: str = Form(...),
    file: UploadFile = File(...),
    use_case: UploadClassroomDatasetUseCase = Depends(upload_classroom_dataset_use_case),
) -> UploadClassroomDatasetResponseDTO:
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        zip_path = Path(tmp.name)
    try:
        _save_upload(file, zip_path)
        return use_case.execute(zip_path, classroom_name)
    finally:
        zip_path.unlink(missing_ok=True)


@router.post("/classroom-imports/process", response_model=ImportClassroomDatasetResponseDTO)
def import_classroom_dataset(
    body: ImportClassroomDatasetDTO,
    use_case: ImportClassroomDatasetUseCase = Depends(import_classroom_dataset_use_case),
) -> ImportClassroomDatasetResponseDTO:
    confined = ImportClassroomDatasetDTO(
        classroom_name=body.classroom_name,
        raw_dir=_confine(body.raw_dir),
        main_table=_confine(body.main_table),
    )
    return use_case.execute(confined)
