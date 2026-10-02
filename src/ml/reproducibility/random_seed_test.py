# seed_all_random_generators é a porta única de semente; cuDNN determinístico e sem benchmark.

from __future__ import annotations

import os
import random

import numpy as np
import torch

from ml.reproducibility.random_seed import seed_all_random_generators


def _draw_all_rngs():
    # Uma amostra de cada um dos quatro RNGs que o contrato deve cobrir.
    return (
        random.random(),
        np.random.rand(5).tolist(),
        torch.rand(5).tolist(),
    )


def test_deterministic_cpu():
    seed_all_random_generators(42, strict=True)
    first = _draw_all_rngs()
    seed_all_random_generators(42, strict=True)
    second = _draw_all_rngs()
    assert first == second


def test_seeds_all_four_rngs():
    seed_all_random_generators(123)
    a_py, a_np, a_torch = _draw_all_rngs()
    seed_all_random_generators(123)
    b_py, b_np, b_torch = _draw_all_rngs()
    # mesma seed -> mesmos números aleatórios em todos os RNGs
    assert a_py == b_py
    assert a_np == b_np
    assert a_torch == b_torch

    seed_all_random_generators(456)
    c_py, c_np, c_torch = _draw_all_rngs()
    # seed diferente -> números aleatórios diferentes em todos os RNGs
    assert c_py != a_py
    assert c_np != a_np
    assert c_torch != a_torch


def test_benchmark_always_off():
    seed_all_random_generators(7, strict=False)
    assert torch.backends.cudnn.benchmark is False
    seed_all_random_generators(7, strict=True)
    assert torch.backends.cudnn.benchmark is False


def test_strict_sets_deterministic_env():
    seed_all_random_generators(42, strict=True)
    assert os.environ["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8"
    assert torch.backends.cudnn.deterministic is True
    assert torch.are_deterministic_algorithms_enabled() is True


def test_non_strict_turns_on_only_the_deterministic_cudnn():
    # O treino na GPU tem o cuDNN determinístico, como o repositório, sem o resto do modo estrito
    seed_all_random_generators(42, strict=True)
    # O padrão do PyTorch é desligado, como num processo novo
    torch.backends.cudnn.deterministic = False
    seed_all_random_generators(99, strict=False)
    assert torch.backends.cudnn.deterministic is True
    assert torch.are_deterministic_algorithms_enabled() is False
