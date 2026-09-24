"""Monta as ReinforcementRecommendation: o que reforçar em aula, do KC mais fraco ao mais forte.

Sem LLM.

O texto usa as mesmas faixas que classificam a matriz, então a recomendação e o dashboard sempre
concordam.
"""

from __future__ import annotations

from api.mastery_dashboard.domain.value_objects.mastery_level import MasteryLevel
from api.mastery_dashboard.domain.services.mastery_classification import classify_mastery_level
from api.mastery_dashboard.domain.value_objects.reinforcement_recommendation import ReinforcementRecommendation

_GUIDANCE = {
    MasteryLevel.LOW: "domínio baixo na turma — priorize reforço",
    MasteryLevel.MEDIUM: "domínio parcial — vale revisar",
    MasteryLevel.HIGH: "domínio consolidado",
}


def recommend_reinforcement(
    kc_means: list[tuple[int, str, float]],
) -> list[ReinforcementRecommendation]:
    """(kc_id, nome, mastery média) por KC → recomendações, da menor mastery para a maior."""
    ranked = sorted(kc_means, key=lambda item: (item[2], item[0]))  # mastery crescente; id desempata
    return [
        ReinforcementRecommendation(
            kc_id=kc_id,
            kc_name=kc_name,
            mean_mastery=mean_mastery,
            text=(
                f"{kc_name}: {_GUIDANCE[classify_mastery_level(mean_mastery)]} "
                f"(mastery média {mean_mastery:.0%})."
            ),
        )
        for kc_id, kc_name, mean_mastery in ranked
    ]
