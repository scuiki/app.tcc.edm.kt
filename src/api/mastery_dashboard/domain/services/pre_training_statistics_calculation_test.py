# As estatísticas pré-treino saem do dado limpo, sem nenhum modelo.

from __future__ import annotations

import pytest

from api.mastery_dashboard.domain.value_objects.pre_training_statistics import PreTrainingStatistics
from api.mastery_dashboard.domain.services.pre_training_statistics_calculation import (
    compile_error_rate_by_assignment,
    learning_curve,
    success_rate_by_assignment,
)


def test_success_rate_is_the_mean_of_is_correct_over_program_runs(a439_mini):
    rates = success_rate_by_assignment(a439_mini)

    runs = a439_mini[a439_mini["event_type"] == "Run.Program"]
    assert rates == {439: pytest.approx(runs["is_correct"].mean())}


def test_the_learning_curve_is_ordered_by_attempt_number(a439_mini):
    curve = learning_curve(a439_mini)

    attempts = list(curve)
    assert attempts == sorted(attempts)
    assert attempts[0] == 0  # a primeira tentativa é a 0
    assert all(0.0 <= v <= 1.0 for v in curve.values())


def test_the_compile_error_rate_is_per_program_run(a439_mini):
    # Compile.Error POR tentativa de execução (CE / Run), não a fração sobre todos os eventos.
    rates = compile_error_rate_by_assignment(a439_mini)

    errors = (a439_mini["event_type"] == "Compile.Error").sum()
    runs = (a439_mini["event_type"] == "Run.Program").sum()
    assert rates[439] == pytest.approx(errors / runs)
    assert rates[439] != pytest.approx((a439_mini["event_type"] == "Compile.Error").mean())


def test_without_data_the_statistics_are_empty_not_an_error():
    empty = PreTrainingStatistics.empty()

    assert (empty.success_rate, empty.learning_curve, empty.compile_error_rate) == ({}, {}, {})
