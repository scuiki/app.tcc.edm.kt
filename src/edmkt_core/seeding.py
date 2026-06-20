"""Centralized seeding for reproducible Code-DKT runs (CORE-03).

Promoted from tcc.edm.kt notebook 06_code_dkt.ipynb cell 3 (set_global_seed). No src/
analog exists in TCC 1 — seeding lived ad-hoc inside the notebook. The notebook set
cudnn.deterministic unconditionally; D-09 makes the strict path conditional.
"""

from __future__ import annotations

import random

import numpy as np
import torch


def set_global_seed(seed: int = 42, strict: bool = False) -> None:
    """Seed random/numpy/torch/cuda once at the start of a run.

    Args:
        seed: global seed (frozen protocol default 42).
        strict: when True, enable bit-deterministic CPU numerics (CORE-03). The
            full strict path is implemented and tested in plan 02; here it is a
            documented stub so callers can already pass the flag.

    cudnn.benchmark is always disabled (Pitfall 2: kernel-selection nondeterminism).
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False  # always off — kernel-selection nondeterminism

    if strict:
        # TODO(plan 02): implement + test the strict determinism path (D-09/CORE-03):
        #   torch.backends.cudnn.deterministic = True
        #   torch.use_deterministic_algorithms(True)
        #   os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        # Gated behind a red→green determinism test in plan 02; not enabled yet.
        raise NotImplementedError(
            "strict determinism is implemented in plan 02 (CORE-03); "
            "call with strict=False until then"
        )
