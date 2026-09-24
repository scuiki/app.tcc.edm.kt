"""As faixas de mastery, os KCs críticos e os alunos em risco."""

from __future__ import annotations

import pytest

from api.mastery_dashboard.domain.value_objects.mastery_level import MasteryLevel
from api.mastery_dashboard.domain.services.mastery_classification import (
    classify_mastery_level,
    find_critical_knowledge_components,
    find_students_at_risk,
)


@pytest.mark.parametrize(
    "mastery, level",
    [
        (0.0, MasteryLevel.LOW),
        (0.399, MasteryLevel.LOW),
        (0.40, MasteryLevel.MEDIUM),  # o limite inferior pertence a medium
        (0.55, MasteryLevel.MEDIUM),
        (0.70, MasteryLevel.MEDIUM),  # 0,70 ainda é medium; só acima vira high
        (0.7001, MasteryLevel.HIGH),
        (1.0, MasteryLevel.HIGH),
    ],
)
def test_levels_at_the_boundaries(mastery, level):
    assert classify_mastery_level(mastery) is level


def test_critical_kcs_come_weakest_first():
    matrix = {("S1", 1): 0.1, ("S2", 1): 0.3, ("S1", 2): 0.7, ("S2", 2): 0.9}

    ranked = find_critical_knowledge_components(matrix)

    assert [kc_id for kc_id, _ in ranked] == [1, 2]
    assert ranked[0][1] == pytest.approx(0.2)
    assert ranked[1][1] == pytest.approx(0.8)


def test_a_student_is_at_risk_with_three_or_more_low_kcs():
    matrix = {
        ("S_risk", 1): 0.1, ("S_risk", 2): 0.2, ("S_risk", 3): 0.3, ("S_risk", 4): 0.9,
        ("S_ok", 1): 0.1, ("S_ok", 2): 0.2, ("S_ok", 3): 0.8, ("S_ok", 4): 0.9,
    }

    assert find_students_at_risk(matrix) == ["S_risk"]
