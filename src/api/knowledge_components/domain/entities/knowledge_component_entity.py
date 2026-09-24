# KnowledgeComponent, um conceito de programação que um problema exige.
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KnowledgeComponent:
    id: int | None
    assignment_id: int
    name: str
    # Grupo 0..N do KCGen-KT, None se o KC foi criado pelo professor, distinto do id do banco.
    group_index: int | None = None
