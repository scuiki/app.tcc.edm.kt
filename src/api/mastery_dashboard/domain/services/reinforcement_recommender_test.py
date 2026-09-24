"""recommend_reinforcement: os KCs de menor mastery primeiro, com texto em pt-BR, sem LLM."""

from __future__ import annotations

from api.mastery_dashboard.domain.services.reinforcement_recommender import recommend_reinforcement


def test_the_weakest_kc_comes_first_with_a_text_that_names_it():
    recommendations = recommend_reinforcement(
        [(20, "Condicionais", 0.50), (30, "Strings", 0.85), (10, "Laços", 0.15)]
    )

    assert [r.kc_name for r in recommendations] == ["Laços", "Condicionais", "Strings"]
    assert recommendations[0].kc_id == 10
    assert recommendations[0].text == "Laços: domínio baixo na turma — priorize reforço (mastery média 15%)."


def test_no_kcs_means_no_recommendations():
    assert recommend_reinforcement([]) == []
