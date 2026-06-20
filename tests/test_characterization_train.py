"""Characterization tests for edmkt_core.models.code_dkt (D-04, CORE-06, D-02).

Smoke/characterization training on CPU over the hermetic fixture: prove the injected
device and on_epoch callback work with behavior-preserving wiring, and that
predict_code_dkt yields the documented pred_df columns. NOT the golden-run — epochs are
reduced for speed; architecture stays frozen.
"""

from __future__ import annotations

import torch.nn as nn

from edmkt_core.evaluation import build_problem_index
from edmkt_core.features import build_vocab, extract_paths_javalang
from edmkt_core.models.code_dkt import predict_code_dkt, train_code_dkt
from edmkt_core.sequences import build_sequences


def _build_inputs(a439_mini):
    sequences = build_sequences(a439_mini, 439)
    cache = {
        csid: extract_paths_javalang(code)
        for csid, code in zip(
            a439_mini["CodeStateID"].astype(str), a439_mini["Code"]
        )
    }
    token_to_idx, path_to_idx = build_vocab(cache)
    vocab = {
        "token_to_idx": token_to_idx,
        "path_to_idx": path_to_idx,
        "node_count": len(token_to_idx),
        "path_count": len(path_to_idx),
    }
    problem_to_idx = build_problem_index(sequences)
    # Architecture frozen; only epoch count reduced for a fast smoke run.
    config = {"hidden_dim": 128, "dropout": 0.1, "lr": 5e-4,
              "batch_size": 128, "epochs": 3, "max_len": 50, "R": 50}
    return sequences, cache, vocab, problem_to_idx, config


def test_train_fires_on_epoch_once_per_epoch(a439_mini, cpu_device):
    sequences, cache, vocab, problem_to_idx, config = _build_inputs(a439_mini)
    calls = []
    model = train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache,
        device=cpu_device,
        on_epoch=lambda epoch, loss: calls.append((epoch, loss)),
    )
    assert isinstance(model, nn.Module)
    assert [c[0] for c in calls] == [1, 2, 3]  # one call per epoch, in order


def test_train_default_on_epoch_is_silent(a439_mini, cpu_device, capsys):
    sequences, cache, vocab, problem_to_idx, config = _build_inputs(a439_mini)
    train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache, device=cpu_device
    )
    # No-op default callback must not print (the old per-epoch print is gone).
    assert capsys.readouterr().out == ""


def test_predict_yields_expected_columns(a439_mini, cpu_device):
    sequences, cache, vocab, problem_to_idx, config = _build_inputs(a439_mini)
    model = train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache, device=cpu_device
    )
    pred_df = predict_code_dkt(
        model, sequences, problem_to_idx, vocab, cache, max_len=50, R=50
    )
    for col in ("correct", "correct_predictions", "is_first_attempt"):
        assert col in pred_df.columns
