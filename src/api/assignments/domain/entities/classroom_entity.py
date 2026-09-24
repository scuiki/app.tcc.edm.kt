"""Classroom: a turma do professor, dona dos dados enviados."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Classroom:
    id: int | None  # None até ser gravada; o repositório devolve o id
    name: str
    created_at: str
