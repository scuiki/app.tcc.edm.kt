# A resposta de POST /classroom-imports, onde o zip foi extraído e o que se encontrou nele.

from __future__ import annotations

from pydantic import BaseModel


class UploadClassroomDatasetResponseDTO(BaseModel):
    classroom_id: int
    raw_dir: str
    main_tables: list[str]  # uma ou mais, o professor escolhe qual importar
    code_snapshots: str | None
