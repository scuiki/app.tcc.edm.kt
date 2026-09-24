"""Etapa 5 do KCGen-KT: a Q-matrix binária problema × KC.

Portado literalmente do TCC 1 (notebook 03b_kc_generation, célula 19). Sem I/O e sem LLM: a
Q-matrix é reconstruída de forma determinística a partir dos KCs candidatos e do agrupamento
guardados, e tem de bater célula a célula com o qmatrix_A*.csv do TCC 1.
"""

from __future__ import annotations

import pandas as pd


def build_qmatrix(problem_ids, candidate_kcs_by_problem: dict, kc_grouping: dict) -> pd.DataFrame:
    """Q-matrix (problem_id × kc_0..kc_N): célula [p, kc_i] = 1 se algum KC de p caiu no grupo i.

    Um problema sem KC candidato fica com a linha toda zerada. Recusar isso é decisão de quem
    valida a Q-matrix, não deste construtor, que nunca inventa vínculos.
    """
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
