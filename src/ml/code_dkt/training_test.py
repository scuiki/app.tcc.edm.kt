# Treino curto do Code-DKT em CPU (poucas épocas); confere device e on_epoch, não é regressão.

from __future__ import annotations

import torch.nn as nn

from ml.code_dkt.training import train_code_dkt


def test_train_fires_on_epoch_once_per_epoch(training_inputs, cpu_device):
    sequences, cache, vocab, problem_to_idx, config = training_inputs
    calls = []
    model = train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache,
        device=cpu_device,
        on_epoch=lambda epoch, loss: calls.append((epoch, loss)),
    )
    assert isinstance(model, nn.Module)
    assert [c[0] for c in calls] == [1, 2, 3]  # uma chamada por época, em ordem


def test_train_default_on_epoch_is_silent(training_inputs, cpu_device, capsys):
    sequences, cache, vocab, problem_to_idx, config = training_inputs
    train_code_dkt(
        sequences, problem_to_idx, vocab, config, cache, device=cpu_device
    )
    # O callback padrão no-op não deve imprimir nada (o antigo print por época sumiu).
    assert capsys.readouterr().out == ""
