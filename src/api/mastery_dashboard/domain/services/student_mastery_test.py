# A média do aluno é sobre problemas, e os mais fracos vêm em ordem com desempate estável.

from __future__ import annotations

import pytest

from api.mastery_dashboard.domain.services.student_mastery import (
    mean_mastery_by_student,
    weakest_knowledge_components,
)


def test_the_mean_is_over_the_problems_of_each_student():
    matrix = {("S1", 1): 0.2, ("S1", 2): 0.6, ("S2", 1): 1.0}

    assert mean_mastery_by_student(matrix) == {"S1": pytest.approx(0.4), "S2": pytest.approx(1.0)}


def test_the_weakest_come_first_and_ties_break_by_id():
    weakest = weakest_knowledge_components({30: 0.5, 10: 0.2, 20: 0.2, 40: 0.9})

    assert weakest == [(10, 0.2), (20, 0.2), (30, 0.5)]


def test_fewer_concepts_than_requested_is_fine():
    assert weakest_knowledge_components({7: 0.3}) == [(7, 0.3)]
