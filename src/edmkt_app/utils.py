"""Helpers internos puros compartilhados pela app layer (IN-01).

`progsnap_aid` e `slug` derivam, de um nome de assignment/turma INTERNO, o AssignmentID do
ProgSnap2 (sufixo numérico) e o slug de diretório — nunca de caminho de cliente. A lógica é a
mesma replicada em train.py/mastery_service.py/eda.py/kc_pipeline.py; este módulo é a versão
PÚBLICA e única, para call sites fora do módulo dono não cruzarem a fronteira do underscore.

Mantido livre de torch/persistence (igual a eda.py): import barato, sem acoplar a stack de ML.
"""

from __future__ import annotations

import re


def slug(name: str) -> str:
    """Slug de diretório a partir de um nome interno (mesma forma de train._slug)."""
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "turma"


def progsnap_aid(assignment_name: str) -> int:
    """AssignmentID do ProgSnap2 = sufixo numérico do nome (igual a train._progsnap_aid)."""
    m = re.search(r"(\d+)", assignment_name)
    if m is None:
        raise ValueError(f"AssignmentID não derivável do nome: {assignment_name!r}")
    return int(m.group(1))
