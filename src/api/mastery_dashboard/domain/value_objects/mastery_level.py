# A faixa de domínio mostrada no dashboard (baixo, médio, alto).

from __future__ import annotations

from enum import StrEnum


class MasteryLevel(StrEnum):
    LOW = "low"  # abaixo de 0,40
    MEDIUM = "medium"  # de 0,40 a 0,70, inclusive
    HIGH = "high"  # acima de 0,70
