# Porta única de semente do Code-DKT; o cuDNN é determinístico sempre, e o resto só no estrito.

from __future__ import annotations

import os
import random

import numpy as np
import torch


def seed_all_random_generators(seed: int = 42, strict: bool = False) -> None:
    # Semeia random, numpy, torch e cuda; strict=True força o resultado numérico bit a bit (só CPU).
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False  # desligado, escolha de kernel dele não é determinista
    # Como o repositório oficial, também no treino da GPU, que roda no modo não estrito
    torch.backends.cudnn.deterministic = True

    if strict:
        torch.use_deterministic_algorithms(True)
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"  # exigido pelo cuBLAS GEMM determinista
    else:
        # Reset explícito, um treino estrito anterior não pode vazar determinismo pro não estrito.
        torch.use_deterministic_algorithms(False)
