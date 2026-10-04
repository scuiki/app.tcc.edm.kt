# Etapa 3 do KCGen-KT, agrupa nomes de KC parecidos com SBERT e HAC, no número de grupos do paper.

from __future__ import annotations

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist

# O nível médio que o paper escolheu na CodeWorkout, 50 grupos para 103 nomes únicos
MEDIUM_ABSTRACTION_RATIO = 50 / 103


def kc_group_count(n_names: int) -> int:
    # A proporção do paper sobre os nomes do exercício, arredondada, com pelo menos um grupo
    return max(1, round(MEDIUM_ABSTRACTION_RATIO * n_names))


def group_similar_kcs(embeddings: np.ndarray, n_groups: int) -> np.ndarray:
    # Clustering hierárquico (cosseno, average linkage) em n_groups; rótulos a partir de 0.
    if len(embeddings) == 1:
        # O HAC precisa de dois nomes, e um nome só é o próprio grupo
        return np.zeros(1, dtype=int)
    dist_condensed = pdist(embeddings, metric="cosine")
    dist_condensed = np.clip(dist_condensed, 0, None)  # corrige negativos de ponto flutuante
    Z = linkage(dist_condensed, method="average")
    labels = fcluster(Z, t=n_groups, criterion="maxclust")
    return labels - 1  # o fcluster do scipy começa em 1
