"""A faixa de domínio que o dashboard mostra. Quem classifica é `services/mastery_classification.py`."""

from __future__ import annotations

from enum import StrEnum


class MasteryLevel(StrEnum):
    LOW = "low"  # abaixo de 0,40
    MEDIUM = "medium"  # de 0,40 a 0,70, inclusive
    HIGH = "high"  # acima de 0,70
