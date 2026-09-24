"""Etapa 3 do KCGen-KT: agrupar os nomes de KC parecidos.

Portado literalmente do TCC 1 (notebook 03b_kc_generation, célula 12). Ciência congelada:
embeddings SBERT (all-MiniLM-L6-v2) + clustering hierárquico (cosseno, average linkage), com o
número de grupos escolhido pelo silhouette entre 10, 12 e 15. Os embeddings chegam prontos: este
módulo não baixa nem carrega o modelo SBERT.
"""

from __future__ import annotations

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist
from sklearn.metrics import silhouette_score

# Os candidatos de número de grupos da seleção por silhouette. NÃO alterar: quem chama usa o
# menor deles para decidir quando nem vale agrupar.
CANDIDATE_GROUP_COUNTS = (10, 12, 15)


def group_similar_kcs(embeddings: np.ndarray, n_groups: int) -> np.ndarray:
    """Clustering hierárquico (cosseno, average linkage) em n_groups; rótulos a partir de 0."""
    dist_condensed = pdist(embeddings, metric="cosine")
    dist_condensed = np.clip(dist_condensed, 0, None)  # corrige negativos de ponto flutuante
    Z = linkage(dist_condensed, method="average")
    labels = fcluster(Z, t=n_groups, criterion="maxclust")
    return labels - 1  # o fcluster do scipy começa em 1


def choose_kc_group_count(embeddings: np.ndarray, candidates=CANDIDATE_GROUP_COUNTS):
    """O número de grupos com o maior silhouette médio (Rousseeuw, 1987)."""
    n_kc_names = len(embeddings)
    # Sem candidato menor que o número de nomes não há o que avaliar, e max() de dict vazio daria
    # um erro opaco. Falha clara: quem chama já desvia antes para "um grupo por nome".
    if not any(n < n_kc_names for n in candidates):
        raise ValueError(
            f"n_kc_names={n_kc_names} abaixo do menor candidato {min(candidates)}: "
            "nada a clusterizar (use o caminho sem-clustering no caller)"
        )
    scores: dict = {}
    for n in candidates:
        if n >= n_kc_names:  # candidato que forçaria grupos de um elemento só
            continue
        labels = group_similar_kcs(embeddings, n)
        if len(set(labels)) < 2:
            scores[n] = -1.0
            continue
        scores[n] = float(silhouette_score(embeddings, labels, metric="cosine"))
    best_n = max(scores, key=lambda k: scores[k])
    return best_n, scores
