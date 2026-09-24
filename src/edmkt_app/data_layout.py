"""Onde cada coisa de uma turma mora em disco. O único lugar que monta caminhos sob `data/`.

    data/<turma_slug>/
        raw/                              o .zip do professor extraído, intocado
        clean/assignment_<N>.parquet      o dado limpo, um arquivo por assignment
        cache/paths/<code_state_id>.pkl   paths de AST já extraídos
        kc/assignment_<N>/                respostas do LLM guardadas da geração de KCs
        models/<assignment_id>/v<K>/      as versões de modelo treinadas

`<N>` é o AssignmentID do ProgSnap2; `<assignment_id>` é o id do banco. Cada componente vem de
um value object ou de um inteiro interno, nunca de texto do cliente.

`settings.DATA_ROOT` é lido em tempo de chamada, não no import: o override do subprocess (a
partir do env) e o monkeypatch dos testes precisam alcançar estas funções.
"""

from __future__ import annotations

from pathlib import Path

from edmkt_app import settings
from edmkt_app.values import ProgSnapAssignmentId, TurmaSlug


def classroom_dir(turma_slug: TurmaSlug) -> Path:
    return settings.DATA_ROOT / turma_slug


def raw_upload_dir(turma_slug: TurmaSlug) -> Path:
    return classroom_dir(turma_slug) / "raw"


def cleaned_submissions_dir(turma_slug: TurmaSlug) -> Path:
    return classroom_dir(turma_slug) / "clean"


def cleaned_submissions_path(
    turma_slug: TurmaSlug, progsnap_aid: ProgSnapAssignmentId | int
) -> Path:
    return cleaned_submissions_dir(turma_slug) / f"assignment_{progsnap_aid}.parquet"


def ast_path_cache_dir(turma_slug: TurmaSlug) -> Path:
    return classroom_dir(turma_slug) / "cache" / "paths"


def llm_cache_dir(turma_slug: TurmaSlug, progsnap_aid: ProgSnapAssignmentId) -> Path:
    return classroom_dir(turma_slug) / "kc" / f"assignment_{progsnap_aid}"


def trained_models_dir(turma_slug: TurmaSlug) -> Path:
    return classroom_dir(turma_slug) / "models"
