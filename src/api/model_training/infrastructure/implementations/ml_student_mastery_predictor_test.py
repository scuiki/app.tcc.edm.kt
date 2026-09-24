# MlStudentMasteryPredictor, a mastery por KC agrega a previsão de cada problema pelos KCs dele.

from __future__ import annotations

import pytest

from ml.mastery.mastery_aggregation import aggregate_student_mastery


def test_mastery_aggregates_the_problem_predictions_by_kc(
    trained_artifact, real_mastery_predictor, seed_cleaned_submissions, training_dataset_of
):
    seed_cleaned_submissions()
    dataset = training_dataset_of(trained_artifact.assignment_id)
    kcs_by_problem: dict[int, list[int]] = {}
    for binding in trained_artifact.problem_kcs:
        kcs_by_problem.setdefault(binding.problem_id, []).append(binding.kc_id)

    matrix = real_mastery_predictor.predict_mastery(
        trained_artifact.trained_model, dataset, kcs_by_problem
    )

    predictions = real_mastery_predictor.predict(trained_artifact.trained_model, dataset)
    assert matrix == pytest.approx(aggregate_student_mastery(predictions, kcs_by_problem))
    assert matrix
