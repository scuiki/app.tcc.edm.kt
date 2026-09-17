"""Frozen Code-DKT hyperparameters (Shi et al. 2022 protocol).

Promoted from tcc.edm.kt notebook 06_code_dkt.ipynb cell 3 (DEFAULT_CONFIG) and the
grid BEST_CONFIG (cell 24). No src/ analog exists in TCC 1.
"""

from __future__ import annotations

from types import MappingProxyType

# CLAUDE.md §Constraints / Shi et al. (2022) frozen protocol.
# dropout=0.1 follows the FROZEN protocol — NOT the notebook's 0.0 default.
#
# Open Question Q1 (RESEARCH): the exact config that produced 73.27% must be
# confirmed against results/code_dkt_results_multirun.pkl (the 73.27% reference
# came from the grid BEST_CONFIG, not the default). The regression test (plan 06) is
# the arbiter; if it lands outside [70.27, 76.27] revisit dropout/lr here.
_FROZEN = {
    "R": 50,
    "max_path_length": 8,
    "max_path_width": 2,
    "node_embed_dim": 100,
    "path_embed_dim": 100,
    "hidden_dim": 128,
    "dropout": 0.1,
    "lr": 5e-4,
    "epochs": 40,
    "batch_size": 128,
    "grad_clip": 10,
    "max_len": 50,
    "seed": 42,
}

# MappingProxyType blocks mutation of the public mapping.
FROZEN_CONFIG = MappingProxyType(_FROZEN)
