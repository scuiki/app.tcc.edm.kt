# Ported verbatim from tcc.edm.kt — notebooks/03b_kc_generation.ipynb cell 12.
# Frozen science (KC-01): SBERT all-MiniLM-L6-v2 + HAC (cosine, average linkage) selected by
# silhouette over n_clusters ∈ {10,12,15}. The SBERT embeddings are INJECTED (passed in), never
# imported here — the pure core stays free of the sentence-transformers I/O/model-download.

from __future__ import annotations

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist
from sklearn.metrics import silhouette_score

# Ciência congelada (KC-01, Shi et al. / TCC): os candidatos de n_clusters da seleção por
# silhouette. NÃO alterar — o caller usa min() destes para decidir o caminho sem-clustering (CR-01).
CANDIDATE_N_CLUSTERS = (10, 12, 15)


def _cluster_with_n(embeddings: np.ndarray, n_clusters: int) -> np.ndarray:
    """HAC with cosine distance (average linkage), returns 0-indexed labels."""
    dist_condensed = pdist(embeddings, metric="cosine")
    dist_condensed = np.clip(dist_condensed, 0, None)  # fix floating-point negatives
    Z = linkage(dist_condensed, method="average")
    labels = fcluster(Z, t=n_clusters, criterion="maxclust")
    return labels - 1  # scipy fcluster is 1-indexed


def select_best_n_clusters(embeddings: np.ndarray, candidates=CANDIDATE_N_CLUSTERS):
    """Pick the n_clusters maximising the average silhouette (Rousseeuw, 1987)."""
    n_unique = len(embeddings)
    # Sem candidato n < n_unique não há o que avaliar: o silhouette/HAC não se aplica e max() de
    # dict vazio estouraria um erro opaco (CR-01). Falha CLARA — o caller (_kc_body) já desvia
    # para o caminho sem-clustering (um cluster por nome único) ANTES de chamar aqui.
    if not any(n < n_unique for n in candidates):
        raise ValueError(
            f"n_unique={n_unique} abaixo do menor candidato {min(candidates)}: "
            "nada a clusterizar (use o caminho sem-clustering no caller)"
        )
    scores: dict = {}
    for n in candidates:
        if n >= n_unique:  # skip candidates that would force singleton clusters (Pitfall 5)
            continue
        labels = _cluster_with_n(embeddings, n)
        if len(set(labels)) < 2:
            scores[n] = -1.0
            continue
        scores[n] = float(silhouette_score(embeddings, labels, metric="cosine"))
    best_n = max(scores, key=lambda k: scores[k])
    return best_n, scores
