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
    # O nome que a extração gerou, em inglês e em minúsculas, e o `name` é o mostrado em português
    generated_name: str | None = None
    # A data da última edição do conceito pelo professor, vazia no que ninguém editou
    updated_at: str | None = None

    @property
    def is_generated_by_llm(self) -> bool:
        # Hoje só o renomear grava o `updated_at`, e outra edição do `kc` pede rever esta regra
        return self.generated_name is not None and self.updated_at is None
