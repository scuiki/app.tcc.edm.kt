"""edmkt_core — pure, test-driven scientific core for EDM·KT (TCC 2).

Faithful port of the TCC 1 Code-DKT pipeline (tcc.edm.kt @ 0e8807c), locked under
characterization tests before any correction. Public surface is the DIP boundary the
FastAPI app depends inward on.
"""

from edmkt_core.config import FROZEN_CONFIG
from edmkt_core.seeding import set_global_seed

# train_and_evaluate / split_by_subject become public glue in plans 04/05 (pipeline.py).
__all__ = ["FROZEN_CONFIG", "set_global_seed"]
