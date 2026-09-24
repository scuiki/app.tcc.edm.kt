# Onde cada coisa de uma turma mora em disco, o único lugar que monta caminhos sob `data/`.
from __future__ import annotations

import os
from pathlib import Path

from api.shared.infrastructure import settings

# Slug da turma e AssignmentID chegam como value objects, aqui só viram componentes de caminho.
Slug = str | os.PathLike


# O dado limpo não mora aqui (fica em submission); lê DATA_ROOT em tempo de chamada, não no import.
def classroom_dir(classroom_slug: Slug) -> Path:
    return settings.DATA_ROOT / classroom_slug


def raw_upload_dir(classroom_slug: Slug) -> Path:
    return classroom_dir(classroom_slug) / "raw"


def ast_path_cache_dir(classroom_slug: Slug) -> Path:
    return classroom_dir(classroom_slug) / "cache" / "paths"


def llm_cache_dir(classroom_slug: Slug, progsnap_assignment_id: int) -> Path:
    return classroom_dir(classroom_slug) / "kc" / f"assignment_{progsnap_assignment_id}"


def trained_models_dir(classroom_slug: Slug) -> Path:
    return classroom_dir(classroom_slug) / "models"
