"""O que um treino devolve. O modelo treinado é opaco para a aplicação."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingOutcome:
    model: object  # o CodeDKTModel treinado; só a infraestrutura sabe o que é
    vocab: dict
    hyperparameters: dict
    first_attempt_auc: float
    java_parse_rate: float
