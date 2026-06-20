"""edmkt_core — pure, test-driven scientific core for EDM·KT (TCC 2).

Faithful port of the TCC 1 Code-DKT pipeline (tcc.edm.kt @ 0e8807c), locked under
characterization tests before any correction. Public surface is the DIP boundary the
FastAPI app depends inward on.
"""

from edmkt_core.config import FROZEN_CONFIG
from edmkt_core.pipeline import split_by_subject, train_and_evaluate
from edmkt_core.seeding import set_global_seed

# Public surface = the DIP boundary the FastAPI app depends inward on (D-01, D-03).
__all__ = [
    "FROZEN_CONFIG",
    "set_global_seed",
    "split_by_subject",
    "train_and_evaluate",
]
