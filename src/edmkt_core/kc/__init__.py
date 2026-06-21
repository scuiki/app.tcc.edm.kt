"""edmkt_core.kc — pure KCGen-KT pipeline ported from tcc.edm.kt (notebook 03b).

Frozen science (KC-01): diversity sampling (n=5, first-correct) → SBERT/HAC clustering by
silhouette → Q-matrix builder. The pipeline is PURE (DIP, Phase 1): it declares the LLMClient
port and never imports edmkt_app, anthropic, subprocess, or the filesystem — the LLM transport
is injected by the app layer.
"""

from edmkt_core.kc.clustering import select_best_n_clusters
from edmkt_core.kc.generation import KC_SCHEMA, EmptyKCError, generate_kcs_for_problem
from edmkt_core.kc.labeling import label_cluster
from edmkt_core.kc.ports import LLMClient
from edmkt_core.kc.qmatrix import build_qmatrix
from edmkt_core.kc.sampling import diversity_sample

__all__ = [
    "KC_SCHEMA",
    "EmptyKCError",
    "LLMClient",
    "build_qmatrix",
    "diversity_sample",
    "generate_kcs_for_problem",
    "label_cluster",
    "select_best_n_clusters",
]
