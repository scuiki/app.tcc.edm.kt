# A predição do Code-DKT devolve as colunas documentadas.

from __future__ import annotations

from ml.code_dkt.prediction import predict_code_dkt, predict_current_state
from ml.code_dkt.training import train_code_dkt


def test_predict_yields_expected_columns(training_inputs, cpu_device):
    sequences, cache, vocab, problem_to_idx, config = training_inputs
    model = train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache, device=cpu_device
    )
    pred_df = predict_code_dkt(
        model, sequences, problem_to_idx, vocab, cache, max_len=50, R=50
    )
    for col in ("is_correct", "predicted_correct_probability", "is_first_attempt"):
        assert col in pred_df.columns


def test_current_state_covers_every_student_and_every_problem(training_inputs, cpu_device):
    sequences, cache, vocab, problem_to_idx, config = training_inputs
    model = train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache, device=cpu_device
    )

    state = predict_current_state(
        model, sequences, problem_to_idx, vocab, cache, max_len=50, R=50
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
