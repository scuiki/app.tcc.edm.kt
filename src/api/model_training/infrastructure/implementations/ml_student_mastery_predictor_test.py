# MlStudentMasteryPredictor, o estado atual de cada aluno em cada problema do assignment.

from __future__ import annotations


def test_current_mastery_covers_every_student_and_problem(
    trained_artifact, real_mastery_predictor, seed_cleaned_submissions, training_dataset_of
):
    seed_cleaned_submissions()
    dataset = training_dataset_of(trained_artifact.assignment_id)

    matrix = real_mastery_predictor.predict_current_mastery(
        trained_artifact.trained_model, dataset
    )

    students = set(dataset.events["student_id"].astype(str))
    problems = set(dataset.events["problem_id"].astype(int))
    assert set(matrix) == {(s, p) for s in students for p in problems}
    assert all(isinstance(s, str) and isinstance(p, int) for s, p in matrix)
    assert all(0.0 <= v <= 1.0 for v in matrix.values())
