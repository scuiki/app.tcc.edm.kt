# As estatísticas das submissões disponíveis antes de qualquer treino, direto do dado limpo.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PreTrainingStatistics:
    success_rate: dict[int, float]  # por AssignmentID do dataset
    learning_curve: dict[int, float]  # por número da tentativa
    compile_error_rate: dict[int, float]  # por AssignmentID do dataset

    @classmethod
    def empty(cls) -> "PreTrainingStatistics":
        # Sem dado limpo ainda, estatísticas vazias, não um erro.
        return cls(success_rate={}, learning_curve={}, compile_error_rate={})
