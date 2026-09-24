# TrainedModelInfo acompanha todo número vindo do modelo (first-attempt AUC e data do treino).

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainedModelInfo:
    first_attempt_auc: float | None
    trained_at: str | None

    @classmethod
    def not_trained(cls) -> "TrainedModelInfo":
        return cls(first_attempt_auc=None, trained_at=None)
