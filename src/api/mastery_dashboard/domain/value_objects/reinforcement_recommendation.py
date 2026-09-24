"""Uma recomendação de reforço para um KC. Quem monta é `services/reinforcement_recommender.py`."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReinforcementRecommendation:
    kc_id: int
    kc_name: str
    mean_mastery: float
    text: str  # em pt-BR, exibido como está
