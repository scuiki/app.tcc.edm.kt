"""Centralized seeding for reproducible Code-DKT runs (CORE-03).

Promoted from tcc.edm.kt notebook 06_code_dkt.ipynb cell 3 (set_global_seed). No src/
analog exists in TCC 1 — seeding lived ad-hoc inside the notebook. The notebook set
cudnn.deterministic unconditionally; D-09 makes the strict path conditional.
"""

from __future__ import annotations

import os
import random

import numpy as np
import torch


def set_global_seed(seed: int = 42, strict: bool = False) -> None:
    """Seed random/numpy/torch/cuda once at the start of a run.

    Args:
        seed: global seed (frozen protocol default 42).
        strict: when True, force bit-deterministic numerics (CORE-03) — for CPU
            unit tests. D-09 keeps this conditional so GPU training trusts its
            ±3pp band (D-10) instead of paying the strict-determinism cost.

    cudnn.benchmark is always disabled (Pitfall 2: kernel-selection nondeterminism).
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
        # Explicit reset keeps the call idempotent: a prior strict run must not leak
        # forced determinism into a non-strict (GPU ±3pp, D-10) run.
        torch.use_deterministic_algorithms(False)
