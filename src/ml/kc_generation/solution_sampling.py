# Etapa 1 do KCGen-KT, escolhe até 5 soluções corretas de um problema, uma por grupo do CodeBERT.

from __future__ import annotations

import random
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering

SEED = 42

# As 5 soluções por problema do experimento principal do paper
SOLUTIONS_PER_PROBLEM = 5


def select_sample_solutions(
    correct_runs: pd.DataFrame,
    embed: Callable[[list[str]], np.ndarray],
    n: int = SOLUTIONS_PER_PROBLEM,
) -> list[dict]:
    # As execuções corretas do problema, em ordem de tempo, viram até n grupos, e sai uma de cada
    ordered = correct_runs.sort_values(["submitted_at", "submission_id"])
    runs = ordered.to_dict("records")
    distinct_codes = list(dict.fromkeys(str(run["code"]) for run in runs))
    n_groups = min(n, len(distinct_codes))
    if n_groups == 0:
        return []
    # Um gerador novo por problema, para a amostra de um problema não depender dos outros
    rng = random.Random(SEED)
    if n_groups == 1:
        return [rng.choice(runs)]
    # Cada código distinto passa uma vez pelo CodeBERT, então cópias iguais ficam no mesmo grupo
    vector_of = dict(zip(distinct_codes, embed(distinct_codes)))
    vectors = np.stack([vector_of[str(run["code"])] for run in runs])
    labels = AgglomerativeClustering(
        n_clusters=n_groups, metric="cosine", linkage="average"
    ).fit_predict(vectors)
    return [
        rng.choice([run for run, label in zip(runs, labels) if label == group])
        for group in sorted(set(labels))
    ]
