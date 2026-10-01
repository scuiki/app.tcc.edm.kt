# Treino curto do Code-DKT em CPU (poucas épocas); confere device e on_epoch, não é regressão.

from __future__ import annotations

import torch
import torch.nn as nn

from ml.code_dkt.model import CodeDKTModel
from ml.code_dkt.training import train_code_dkt
from ml.reproducibility.random_seed import seed_all_random_generators


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


def test_the_batch_in_chunks_gives_the_gradient_of_the_whole_batch(
    training_inputs, cpu_device, monkeypatch
):
    # Sem dropout, o lote em pedaços de 1 aluno dá o gradiente do lote inteiro, que pesa os eventos
    sequences, cache, vocab, problem_to_idx, config = training_inputs
    monkeypatch.setattr(torch.nn.functional, "dropout", lambda x, *args, **kwargs: x)
    recorded = []

    class _GradientRecorder:
        # Grava o gradiente do único passo, que o Adam normalizaria e esconderia
        def __init__(self, params, lr):
            self.params = list(params)

        def zero_grad(self):
            for p in self.params:
                p.grad = None

        def step(self):
            recorded.append([None if p.grad is None else p.grad.clone() for p in self.params])

    monkeypatch.setattr(torch.optim, "Adam", _GradientRecorder)
    forward_sizes: dict[int, list[int]] = {}
    real_forward = CodeDKTModel.forward
    for chunk_size in (128, 1):
        sizes = forward_sizes.setdefault(chunk_size, [])

        def recording_forward(self, x, sizes=sizes):
            sizes.append(x.shape[0])
            return real_forward(self, x)

        monkeypatch.setattr(CodeDKTModel, "forward", recording_forward)
        seed_all_random_generators(42, strict=True)
        train_code_dkt(
            sequences, problem_to_idx, vocab,
            {**config, "epochs": 1, "batch_chunk_size": chunk_size}, cache, device=cpu_device,
        )

    whole, chunked = recorded
    assert len(sequences) <= 128 and len(recorded) == 2
    assert forward_sizes == {128: [len(sequences)], 1: [1] * len(sequences)}
    for g_whole, g_chunked in zip(whole, chunked):
        if g_whole is None:
            assert g_chunked is None
        else:
            torch.testing.assert_close(g_chunked, g_whole, rtol=1e-4, atol=1e-6)
