# A predição do Code-DKT devolve as colunas documentadas.

from __future__ import annotations

import pandas as pd

from ml.code_dkt import model_input, prediction
from ml.code_dkt.ast_paths import build_ast_path_vocabulary, extract_ast_paths
from ml.code_dkt.model import CodeDKTModel
from ml.code_dkt.prediction import predict_code_dkt, predict_current_state
from ml.code_dkt.problem_index import build_problem_index
from ml.code_dkt.student_sequences import build_student_sequences
from ml.code_dkt.training import train_code_dkt
from tests.fixtures.sample_data import JAVA_LONG, JAVA_OK_A, cleaned_row, with_cleaned_dtypes


def test_predict_yields_expected_columns(training_inputs, cpu_device):
    sequences, cache, vocab, problem_to_idx, config = training_inputs
    model = train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache, device=cpu_device
    )
    pred_df = predict_code_dkt(
        model, sequences, problem_to_idx, vocab, cache, max_len=50, R=100
    )
    for col in ("is_correct", "predicted_correct_probability", "is_first_attempt"):
        assert col in pred_df.columns


def test_current_state_covers_every_student_and_every_problem(training_inputs, cpu_device):
    sequences, cache, vocab, problem_to_idx, config = training_inputs
    model = train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache, device=cpu_device
    )

    state = predict_current_state(
        model, sequences, problem_to_idx, vocab, cache, max_len=50, R=100
    )

    # O estado atual não depende de quais problemas o aluno tentou, o vetor cobre todos.
    assert len(state) == len(sequences) * len(problem_to_idx)
    assert set(state["student_id"]) == {str(seq["student_id"]) for seq in sequences}
    for _student, rows in state.groupby("student_id"):
        assert set(rows["problem_id"]) == set(problem_to_idx)
    assert state["predicted_correct_probability"].between(0.0, 1.0).all()


def test_current_state_is_the_last_step_of_the_sequence(training_inputs, cpu_device):
    sequences, cache, vocab, problem_to_idx, config = training_inputs
    model = train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache, device=cpu_device
    )
    seq = sequences[0]
    events = seq["events"]

    whole = predict_current_state(model, [seq], problem_to_idx, vocab, cache)
    # Sem a última tentativa, o estado muda; é a prova de que o último passo entra na conta.
    shorter = {"student_id": seq["student_id"], "events": events.iloc[:-1].reset_index(drop=True)}
    without_last = predict_current_state(model, [shorter], problem_to_idx, vocab, cache)

    assert not whole["predicted_correct_probability"].equals(
        without_last["predicted_correct_probability"]
    )


def test_inference_and_evaluation_go_in_chunks_with_the_same_result(
    training_inputs, cpu_device, monkeypatch
):
    sequences, cache, vocab, problem_to_idx, config = training_inputs
    model = train_code_dkt(sequences, problem_to_idx, vocab, config, cache, device=cpu_device)
    whole_state = predict_current_state(model, sequences, problem_to_idx, vocab, cache)
    whole_preds = predict_code_dkt(model, sequences, problem_to_idx, vocab, cache)

    sizes = []
    real_forward = CodeDKTModel.forward

    def recording_forward(self, x):
        sizes.append(x.shape[0])
        return real_forward(self, x)

    monkeypatch.setattr(CodeDKTModel, "forward", recording_forward)
    monkeypatch.setattr(prediction, "INFERENCE_CHUNK_SIZE", 1)
    state = predict_current_state(model, sequences, problem_to_idx, vocab, cache)
    preds = predict_code_dkt(model, sequences, problem_to_idx, vocab, cache)

    assert sizes == [1] * (2 * len(sequences))
    pd.testing.assert_frame_equal(state, whole_state, rtol=1e-6, atol=1e-7)
    pd.testing.assert_frame_equal(preds, whole_preds, rtol=1e-6, atol=1e-7)


def test_training_evaluation_and_inference_sample_the_paths(cpu_device, monkeypatch):
    # Uma solução com mais de R paths passa pelo sorteio nas três montagens, com a seed recebida
    rows = [
        cleaned_row("S1", 1, "2019-03-01T08:00:00Z", "Run.Program", 0.0, JAVA_LONG, "long"),
        cleaned_row("S1", 2, "2019-03-01T08:01:00Z", "Run.Program", 1.0, JAVA_OK_A, "short"),
    ]
    sequences = build_student_sequences(with_cleaned_dtypes(pd.DataFrame(rows)), 439)
    cache = {"long": extract_ast_paths(JAVA_LONG), "short": extract_ast_paths(JAVA_OK_A)}
    token_to_idx, path_to_idx = build_ast_path_vocabulary(cache)
    vocab = {
        "token_to_idx": token_to_idx, "path_to_idx": path_to_idx,
        "node_count": len(token_to_idx), "path_count": len(path_to_idx),
    }
    problem_to_idx = build_problem_index(sequences)
    config = {"hidden_dim": 8, "epochs": 1, "R": 100, "path_sampling_seed": 7}

    calls = []
    real_sample = model_input.sample_ast_paths

    def recording_sample(paths, *, R, path_sampling_seed):
        if len(paths) > R:
            calls.append((len(paths), R, path_sampling_seed))
        return real_sample(paths, R=R, path_sampling_seed=path_sampling_seed)

    monkeypatch.setattr(model_input, "sample_ast_paths", recording_sample)
    model = train_code_dkt(sequences, problem_to_idx, vocab, config, cache, device=cpu_device)
    predict_code_dkt(model, sequences, problem_to_idx, vocab, cache, R=100, path_sampling_seed=7)
    predict_current_state(
        model, sequences, problem_to_idx, vocab, cache, R=100, path_sampling_seed=7
    )

    assert calls == [(142, 100, 7)] * 3
