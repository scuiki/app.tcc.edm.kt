"""select_best_n_clusters: caminho de dataset pequeno (CR-01).

A ciência congelada (Shi et al. / TCC) fixa os candidatos {10,12,15} — NÃO se alteram. Quando
há menos nomes únicos de KC que o menor candidato viável, não há n < n_unique para avaliar e o
silhouette/HAC não se aplica: a seleção deve falhar de forma CLARA (ValueError) em vez de estourar
um `max() iterable argument is empty` opaco. O caminho real para esses datasets pequenos é NÃO
clusterizar (cada nome único vira seu próprio cluster) — decidido no caller (_kc_body), provado em
test_kc_cli.py. Aqui pinamos só o contrato robusto do selector. O caminho golden (n=15) segue
intacto em test_kc_pipeline.py.
"""

from __future__ import annotations

import numpy as np
import pytest

from edmkt_core.kc.clustering import select_best_n_clusters


def test_fewer_unique_than_smallest_candidate_raises_clear_error():
    # 5 embeddings, candidatos {10,12,15}: todos >= n_unique → nenhum n viável.
    # Antes do fix: max() sobre dict vazio → "max() iterable argument is empty" (opaco).
    rng = np.random.default_rng(42)
    embeddings = rng.random((5, 8)).astype(np.float32)
    with pytest.raises(ValueError, match="n_unique"):
        select_best_n_clusters(embeddings, candidates=(10, 12, 15))


def test_enough_unique_still_selects():
    # >= menor candidato: o selector roda normalmente e devolve um n viável + scores.
    rng = np.random.default_rng(7)
    embeddings = rng.random((20, 8)).astype(np.float32)
    best_n, scores = select_best_n_clusters(embeddings, candidates=(10, 12, 15))
    assert best_n in (10, 12, 15)
    assert scores  # avaliou ao menos um candidato
