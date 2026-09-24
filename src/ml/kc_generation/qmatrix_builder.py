# Etapa 5 do KCGen-KT, a Q-matrix binária problema x KC. Portado do TCC 1, numérica congelada.

from __future__ import annotations

import pandas as pd


def build_qmatrix(problem_ids, candidate_kcs_by_problem: dict, kc_grouping: dict) -> pd.DataFrame:
    # Célula [p, kc_i] = 1 se um KC de p caiu no grupo i; sem KC candidato, a linha fica zerada.
    n_groups = kc_grouping["n_clusters_selected"]
    kc_to_cluster = kc_grouping["kc_to_cluster"]
    col_names = [f"kc_{i}" for i in range(n_groups)]

    rows: dict = {}
    for problem_id in problem_ids:
        row = [0] * n_groups
        if problem_id in candidate_kcs_by_problem:
            for kc in candidate_kcs_by_problem[problem_id]["kcs"]:
                cluster_id = kc_to_cluster.get(kc["name"])
                if cluster_id is not None:
                    row[cluster_id] = 1
        rows[problem_id] = row

    df = pd.DataFrame.from_dict(rows, orient="index", columns=col_names)
    df.index.name = "problem_id"
    return df
