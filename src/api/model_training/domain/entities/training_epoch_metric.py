# TrainingEpochMetric, a loss de uma época; a curva de loss de um treino é a lista delas.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingEpochMetric:
    epoch: int
    train_loss: float
    recorded_at: str
