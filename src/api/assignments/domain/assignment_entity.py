"""Assignment: uma lista de exercícios (ex.: A439), a unidade de treino: um modelo por assignment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AssignmentStatus(StrEnum):
    """Até onde o assignment chegou. Cada transição tem um único dono (docs/GLOSSARY.md)."""

    # Os first-attempts têm uma classe só: o AUC é indefinido, não dá para treinar.
    STATISTICS_ONLY = "statistics_only"
    READY_FOR_KC_GENERATION = "ready_for_kc_generation"
    KC_DRAFT = "kc_draft"  # KCs gerados pelo LLM, aguardando o professor
    KC_APPROVED = "kc_approved"  # o professor aprovou a Q-matrix; pode treinar
    TRAINED = "trained"  # existe um modelo publicado


@dataclass
class Assignment:
    id: int | None  # None até ser gravado; o repositório devolve o id
    classroom_id: int
    name: str
    created_at: str
    status: AssignmentStatus | None = None
    progsnap_assignment_id: int | None = None  # o AssignmentID do dataset, distinto do id do banco
    published_model_id: int | None = None  # a versão de modelo que o dashboard usa
