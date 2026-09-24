"""KnowledgeComponent: um conceito de programação que um problema exige."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KnowledgeComponent:
    id: int | None
    assignment_id: int
    name: str
    # O grupo 0..N do KCGen-KT de onde o KC saiu; None para um KC que o professor criou. É o id
    # que bate com os artefatos do TCC 1 (distinto do id do banco).
    group_index: int | None = None
