# A perda média por aluno de uma época, na mesma escala para qualquer turma; a curva é a lista.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingEpochMetric:
    epoch: int
    train_loss: float
    recorded_at: str
