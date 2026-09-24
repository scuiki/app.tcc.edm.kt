"""TrainedModelInfo: o que acompanha todo número que vem do modelo.

O first-attempt AUC e a data do treino, para o professor saber o quanto confiar na mastery. Sem
modelo publicado, vem vazio, e isso é uma resposta legítima ("ainda não treinado"), não um 404.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainedModelInfo:
    first_attempt_auc: float | None
    trained_at: str | None

    @classmethod
    def not_trained(cls) -> "TrainedModelInfo":
        return cls(first_attempt_auc=None, trained_at=None)
