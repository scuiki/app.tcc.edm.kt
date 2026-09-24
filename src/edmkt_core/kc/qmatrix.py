# Ported verbatim from tcc.edm.kt — notebooks/03b_kc_generation.ipynb cell 19 (build_qmatrix).
# Pure DataFrame builder: no I/O, no LLM. The reproducible scientific object (D-03) is replayed
# deterministically from cached kc_raw + kc_clusters — output must match qmatrix_A*.csv cell-for-cell.

from __future__ import annotations

import pandas as pd


def build_qmatrix(problem_ids, kc_raw: dict, kc_clusters: dict) -> pd.DataFrame:
    """Binary Q-matrix (ProblemID × kc_0..kc_N): cell [p, kc_i]=1 if any KC of p lands in cluster i.

    A problem absent from kc_raw stays an all-zero row — the 0-KC hard-fail is the validation
    layer's decision (KC-04), not this pure builder's (it never invents bindings).
    """
    n_clusters = kc_clusters["n_clusters_selected"]
    kc_to_cluster = kc_clusters["kc_to_cluster"]
    col_names = [f"kc_{i}" for i in range(n_clusters)]

    rows: dict = {}
    for problem_id in problem_ids:
        row = [0] * n_clusters
        if problem_id in kc_raw:
            for kc in kc_raw[problem_id]["kcs"]:
                cluster_id = kc_to_cluster.get(kc["name"])
                if cluster_id is not None:
                    row[cluster_id] = 1
        rows[problem_id] = row

    df = pd.DataFrame.from_dict(rows, orient="index", columns=col_names)
    df.index.name = "problem_id"
    return df
