# As contagens do bloco "o que aconteceu" batem com o dado, problema a problema e aluno a aluno.

from __future__ import annotations

import pandas as pd
import pytest

from api.mastery_dashboard.domain.services.submission_statistics_calculation import (
    compute_knowledge_component_statistics,
    compute_problem_statistics,
    compute_student_activity,
)


def _event(student, problem, minute, event_type="Run.Program", score=0.0):
    return {
        "student_id": student,
        "progsnap_assignment_id": 439,
        "problem_id": problem,
        "code_snapshot_id": f"{student}-{minute}",
        "code": "",
        "score": score,
        "submitted_at": pd.Timestamp("2019-03-01T08:00:00Z") + pd.Timedelta(minutes=minute),
        "event_type": event_type,
        "is_correct": int(event_type == "Run.Program" and score == 1.0),
    }


@pytest.fixture
def cleaned() -> pd.DataFrame:
    # S1 fecha o problema 1 na 3ª execução e o 2 na 1ª; S2 fecha o 1 na 1ª e nunca fecha o 2.
    rows = [
        _event(1, 1, 0), _event(1, 1, 1, "Compile.Error"), _event(1, 1, 2), _event(1, 1, 3, score=1.0),
        _event(1, 2, 4, score=1.0),
        _event(2, 1, 10, score=1.0),
        _event(2, 2, 11), _event(2, 2, 12), _event(2, 2, 13, "Compile.Error"),
    ]
    return pd.DataFrame(rows)


def test_problem_statistics_count_runs_completions_and_attempts(cleaned):
    by_id = {p.problem_id: p for p in compute_problem_statistics(cleaned)}

    one, two = by_id[1], by_id[2]
    assert one.success_rate == pytest.approx(2 / 4)
    assert one.median_attempts_to_complete == pytest.approx(2.0)  # mediana de 3 (S1) e 1 (S2)
    assert (one.students_attempted, one.students_completed) == (2, 2)
    assert one.compile_errors_per_run == pytest.approx(1 / 4)
    assert two.success_rate == pytest.approx(1 / 3)
    assert two.median_attempts_to_complete == pytest.approx(1.0)  # só S1 completou
    assert (two.students_attempted, two.students_completed) == (2, 1)
    assert two.compile_errors_per_run == pytest.approx(1 / 3)


def test_problems_come_from_the_lowest_success_rate_up(cleaned):
    rates = [p.success_rate for p in compute_problem_statistics(cleaned)]

    assert rates == sorted(rates)


def test_a_problem_nobody_completed_has_no_median():
    cleaned = pd.DataFrame([_event(1, 7, 0), _event(2, 7, 1)])

    (only,) = compute_problem_statistics(cleaned)

    assert only.median_attempts_to_complete is None
    assert (only.students_attempted, only.students_completed) == (2, 0)


def test_concept_statistics_pool_the_runs_of_its_problems(cleaned):
    by_id = {k.kc_id: k for k in compute_knowledge_component_statistics(cleaned, {1: [10, 20], 2: [20]})}

    assert by_id[10].success_rate == pytest.approx(2 / 4) and by_id[10].runs == 4
    assert by_id[20].success_rate == pytest.approx(3 / 7) and by_id[20].runs == 7


def test_student_activity_counts_per_student(cleaned):
    activity = compute_student_activity(cleaned)

    assert activity["1"].completed == 2 and activity["1"].attempted == 2
    assert activity["1"].runs == 4 and activity["1"].compile_errors == 1
    assert activity["2"].completed == 1 and activity["2"].attempted == 2
    assert activity["2"].runs == 3 and activity["2"].compile_errors == 1


def test_without_program_runs_everything_is_empty():
    only_errors = pd.DataFrame([_event(1, 1, 0, "Compile.Error")])

    assert compute_problem_statistics(only_errors) == []
    assert compute_knowledge_component_statistics(only_errors, {1: [10]}) == []
    assert compute_student_activity(only_errors) == {}


def test_on_the_reference_sample_the_rates_stay_in_range(a439_mini):
    problems = compute_problem_statistics(a439_mini)

    assert problems and all(0.0 <= p.success_rate <= 1.0 for p in problems)
    assert all(p.students_completed <= p.students_attempted for p in problems)
