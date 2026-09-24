"""Onde cada coisa de uma turma mora em disco. O único lugar que monta caminhos sob `data/`.

    data/<classroom_slug>/            (o dado limpo não mora aqui: fica na tabela submission)
        raw/                              o .zip do professor extraído, intocado
        cache/paths/<code_state_id>.pkl   paths de AST já extraídos
        kc/assignment_<N>/                respostas do LLM guardadas da geração de KCs
        models/<assignment_id>/v<K>/      as versões de modelo treinadas

`<N>` é o AssignmentID do ProgSnap2; `<assignment_id>` é o id do banco. Cada componente vem de
um value object ou de um inteiro interno, nunca de texto do cliente.

`settings.DATA_ROOT` é lido em tempo de chamada, não no import: o override do subprocess (a
partir do env) e o monkeypatch dos testes precisam alcançar estas funções.
"""

from __future__ import annotations

import os
from pathlib import Path

from api.shared.infrastructure import settings

# O slug da turma (ClassroomSlug) e o AssignmentID do dataset chegam como value objects de
# assignments; aqui basta que virem componentes de caminho.
Slug = str | os.PathLike
ProgSnapId = object  # qualquer valor cujo str() é o AssignmentID (int ou ProgSnapAssignmentId)


def classroom_dir(classroom_slug: Slug) -> Path:
    return settings.DATA_ROOT / classroom_slug


def raw_upload_dir(classroom_slug: Slug) -> Path:
    return classroom_dir(classroom_slug) / "raw"


def ast_path_cache_dir(classroom_slug: Slug) -> Path:
    return classroom_dir(classroom_slug) / "cache" / "paths"


def llm_cache_dir(classroom_slug: Slug, progsnap_aid: ProgSnapId) -> Path:
    return classroom_dir(classroom_slug) / "kc" / f"assignment_{progsnap_aid}"


def trained_models_dir(classroom_slug: Slug) -> Path:
    return classroom_dir(classroom_slug) / "models"
