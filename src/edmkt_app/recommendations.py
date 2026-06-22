# Pure reinforcement-ranking in the qmatrix.py style: list/dict in → list out, deterministic.
# D-07: recommendations are a pure ranking — ZERO LLM here (any `import anthropic` is a bug).
# Reuses the critical-KC ordering rule from edmkt_core.mastery (weakest mean mastery first).

from __future__ import annotations

# Templated pt-BR guidance keyed to the weakest KCs; the band word comes from the same cutoffs the
# mastery aggregation classifies against, so message and dashboard agree.
from edmkt_core.mastery import classify_band

_BAND_GUIDANCE = {
    "low": "domínio baixo na turma — priorize reforço",
    "medium": "domínio parcial — vale revisar",
    "high": "domínio consolidado",
}


def recommend_reinforcement(
    kc_means: list[tuple[int, str, float]],
) -> list[dict]:
    """Reinforcement suggestions, lowest-mean-mastery KC first (REC-01).

    Input: (kc_id, kc_name, mean_mastery) per KC. Output: ordered dicts with a non-empty pt-BR text.
    """
    ranked = sorted(kc_means, key=lambda item: (item[2], item[0]))  # mastery asc; kc_id breaks ties

    recs = []
    for kc_id, kc_name, mean_mastery in ranked:
        guidance = _BAND_GUIDANCE[classify_band(mean_mastery)]
        recs.append(
            {
                "kc_id": kc_id,
                "kc_name": kc_name,
                "mean_mastery": mean_mastery,
                "text": f"{kc_name}: {guidance} (mastery média {mean_mastery:.0%}).",
            }
        )
    return recs
