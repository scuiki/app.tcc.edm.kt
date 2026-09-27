# A mastery de um conceito é a média dos problemas que o exigem, com o mesmo peso cada.

from __future__ import annotations

import pytest

from api.mastery_dashboard.domain.services.mastery_by_knowledge_component import (
    aggregate_by_knowledge_component,
)


def test_each_problem_feeds_every_concept_it_requires():
    # O problema 3 exige os dois conceitos, então o valor dele entra nas duas médias.
    matrix = {("S1", 1): 0.2, ("S1", 2): 0.8, ("S1", 3): 0.6}
    kcs_by_problem = {1: [10], 2: [20], 3: [10, 20]}

    by_kc = aggregate_by_knowledge_component(matrix, kcs_by_problem)

    assert by_kc[("S1", 10)] == pytest.approx(0.4)
    assert by_kc[("S1", 20)] == pytest.approx(0.7)


def test_a_single_problem_concept_is_that_problem():
    by_kc = aggregate_by_knowledge_component({("S1", 5): 0.35}, {5: [7]})

    assert by_kc == {("S1", 7): pytest.approx(0.35)}


def test_a_problem_without_concepts_is_ignored():
    by_kc = aggregate_by_knowledge_component({("S1", 1): 0.9, ("S1", 2): 0.1}, {1: [10]})

    assert by_kc == {("S1", 10): pytest.approx(0.9)}
