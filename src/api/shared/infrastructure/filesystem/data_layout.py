# Onde cada coisa de uma turma mora em disco, o único lugar que monta caminhos sob `data/`.
from __future__ import annotations

from pathlib import Path

from api.shared.infrastructure import settings


# Tudo de uma turma fica sob o id dela, que nunca muda; lê DATA_ROOT em tempo de chamada
def classroom_dir(classroom_id: int) -> Path:
    return settings.DATA_ROOT / str(int(classroom_id))


def raw_upload_dir(classroom_id: int, upload_name: str) -> Path:
    # `upload_name` já chega limpo, com a data e o nome do zip de um envio
    return classroom_dir(classroom_id) / "raw" / upload_name


def ast_path_cache_dir(classroom_id: int, assignment_id: int) -> Path:
    # Por assignment, porque dois envios podem ter o mesmo CodeStateID com códigos diferentes
    return classroom_dir(classroom_id) / "cache" / "paths" / str(int(assignment_id))


def llm_cache_dir(classroom_id: int, assignment_id: int) -> Path:
    return classroom_dir(classroom_id) / "kc" / str(int(assignment_id))


def trained_models_dir(classroom_id: int) -> Path:
    return classroom_dir(classroom_id) / "models"
