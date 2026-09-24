# A predição do Code-DKT devolve as colunas documentadas.

from __future__ import annotations

from ml.code_dkt.prediction import predict_code_dkt
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
