"""A única porta de semente de um treino do Code-DKT.

No TCC 1 a semente vivia solta no notebook 06, que ligava cudnn.deterministic sempre. Aqui o
determinismo estrito é opcional: os testes de CPU pedem bit a bit; o treino na GPU confia na
banda de ±3pp do teste de regressão em vez de pagar o custo do determinismo estrito.
"""

from __future__ import annotations

import os
import random

import numpy as np
import torch


def seed_all_random_generators(seed: int = 42, strict: bool = False) -> None:
    """Semeia random, numpy, torch e cuda uma vez, no início do treino.

    `strict=True` força numérica determinística bit a bit (testes de CPU). O cudnn.benchmark fica
    sempre desligado: a escolha de kernel dele não é determinística.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False  # always off — kernel-selection nondeterminism

    if strict:
        torch.backends.cudnn.deterministic = True
        torch.use_deterministic_algorithms(True)
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"  # required by deterministic cuBLAS GEMM
    else:
        # Reset explícito: um treino estrito anterior não pode vazar o determinismo forçado
        # para um treino não estrito (GPU, banda de ±3pp).
        torch.use_deterministic_algorithms(False)
