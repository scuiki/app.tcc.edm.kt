# PublishedModelMastery com a infraestrutura real; cobre o cálculo por versão e as falhas parciais.

from __future__ import annotations

import pytest


class _SpyPredictor:
    # Repassa ao preditor real e registra o que ele recebeu.

    def __init__(self, real) -> None:
        self._real = real
        self.calls = []

    def predict_mastery(self, trained_model, dataset, kcs_by_problem):
        self.calls.append((trained_model, dataset, kcs_by_problem))
        return self._real.predict_mastery(trained_model, dataset, kcs_by_problem)


class _FailsAfterFirstAdd:
    def __init__(self, real) -> None:
        self._real = real
        self._adds = 0

    def add(self, student_mastery) -> int:
        self._adds += 1
        if self._adds > 1:
            raise RuntimeError("disk full no insert da mastery (simulado)")
        return self._real.add(student_mastery)

    def count_by_model(self, trained_model_id: int) -> int:
        return self._real.count_by_model(trained_model_id)

    def list_by_model(self, trained_model_id: int):
        return self._real.list_by_model(trained_model_id)


def _rows(conn, model_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM mastery_prediction WHERE model_artifact_id = ?;", (model_id,)
    ).fetchone()[0]


def test_the_matrix_comes_from_the_predictor_and_carries_the_model_info(
    published_model_mastery, published_assignment, real_mastery_predictor, seed_cleaned_submissions
):
    seed_cleaned_submissions()
    spy = _SpyPredictor(real_mastery_predictor)

    matrix, model_info = published_model_mastery(predictor=spy).of(published_assignment)

    assert matrix
    assert all(isinstance(s, str) and isinstance(k, int) and 0.0 <= v <= 1.0
               for (s, k), v in matrix.items())
    assert model_info.trained_at is not None
    # A Q-matrix aprovada chega ao preditor como problem_id -> [kc_id...].
    _model, _dataset, kcs_by_problem = spy.calls[0]
    assert sorted(kcs_by_problem) == [1, 2, 3] and len(kcs_by_problem[3]) == 2


def test_the_matrix_is_computed_once_per_version(
    published_model_mastery, published_assignment, real_mastery_predictor,
    seed_cleaned_submissions, trained_artifact,
):
    seed_cleaned_submissions()
    spy = _SpyPredictor(real_mastery_predictor)
    mastery = published_model_mastery(predictor=spy)

    first, _ = mastery.of(published_assignment)
    again, _ = mastery.of(published_assignment)

    assert len(spy.calls) == 1  # a segunda leitura serve do banco, sem prever de novo
    assert again == pytest.approx(first)
    assert _rows(trained_artifact.conn, trained_artifact.artifact_id) == len(first)


def test_a_failure_while_saving_leaves_no_partial_matrix(
    published_model_mastery, published_assignment, sqlite_student_masteries,
    seed_cleaned_submissions, trained_artifact,
):
    # Sem a transação, a 1ª linha já gravada serviria para sempre uma matriz truncada como completa.
    seed_cleaned_submissions()

    with pytest.raises(RuntimeError):
        published_model_mastery(
            student_masteries=_FailsAfterFirstAdd(sqlite_student_masteries)
        ).of(published_assignment)

    assert _rows(trained_artifact.conn, trained_artifact.artifact_id) == 0
    matrix, _ = published_model_mastery().of(published_assignment)  # uma leitura limpa recalcula
    assert _rows(trained_artifact.conn, trained_artifact.artifact_id) == len(matrix)


def test_the_version_that_predicts_is_the_version_that_keys_the_rows(
    published_model_mastery, published_assignment, real_mastery_predictor,
    seed_cleaned_submissions, trained_artifact,
):
    seed_cleaned_submissions()
    spy = _SpyPredictor(real_mastery_predictor)

    matrix, _ = published_model_mastery(predictor=spy).of(published_assignment)

    predicting_model = spy.calls[0][0]
    assert predicting_model.id == trained_artifact.artifact_id
    assert _rows(trained_artifact.conn, predicting_model.id) == len(matrix)


def test_inference_sees_only_program_runs(
    published_model_mastery, published_assignment, real_mastery_predictor, seed_cleaned_submissions
):
    # Inferir sobre dado misto traria eventos que o modelo nunca viu no treino.
    seed_cleaned_submissions(with_compile_errors=True)
    spy = _SpyPredictor(real_mastery_predictor)

    published_model_mastery(predictor=spy).of(published_assignment)

    _model, dataset, _qmatrix = spy.calls[0]
    assert set(dataset.events["event_type"].unique()) == {"Run.Program"}


def test_without_a_published_model_the_matrix_is_empty(published_model_mastery, published_assignment):
    published_assignment.published_model_id = None

    matrix, model_info = published_model_mastery().of(published_assignment)

    assert matrix == {}
    assert (model_info.first_attempt_auc, model_info.trained_at) == (None, None)
