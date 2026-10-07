# AssignmentStatus, até onde o assignment chegou; cada transição tem um único dono.

from __future__ import annotations

from enum import StrEnum


class AssignmentStatus(StrEnum):
    # Os first-attempts têm uma classe só, então o AUC é indefinido e não dá para treinar.
    STATISTICS_ONLY = "statistics_only"
    READY_FOR_KC_GENERATION = "ready_for_kc_generation"
    KC_DRAFT = "kc_draft"  # KCs gerados pelo LLM, aguardando o professor
    KC_APPROVED = "kc_approved"  # o professor aprovou os KCs; pode treinar
    TRAINED = "trained"  # existe um modelo publicado
