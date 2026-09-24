"""choose_kc_group_count e o agrupamento de KCs.

Os candidatos 10, 12 e 15 são ciência congelada. Com menos nomes de KC que o menor candidato, não há
o que avaliar: a escolha falha com um ValueError claro (quem chama desvia antes para "um grupo por
nome"). Com o SBERT disponível, a escolha converge no número de grupos do TCC 1 para o A439 (15).
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from ml.kc_generation.kc_grouping import choose_kc_group_count


def test_fewer_unique_than_smallest_candidate_raises_clear_error():
    # 5 embeddings, candidatos {10,12,15}: todos >= n_unique → nenhum n viável.
    # Antes do fix: max() sobre dict vazio → "max() iterable argument is empty" (opaco).
    rng = np.random.default_rng(42)
    embeddings = rng.random((5, 8)).astype(np.float32)
    with pytest.raises(ValueError, match="n_kc_names"):
        choose_kc_group_count(embeddings, candidates=(10, 12, 15))


def test_enough_unique_still_selects():
    # >= menor candidato: o selector roda normalmente e devolve um n viável + scores.
    rng = np.random.default_rng(7)
    embeddings = rng.random((20, 8)).astype(np.float32)
    best_n, scores = choose_kc_group_count(embeddings, candidates=(10, 12, 15))
    assert best_n in (10, 12, 15)
    assert scores  # avaliou ao menos um candidato


def _load(kc_reference_dir, name):
    return json.loads((kc_reference_dir / name).read_text())


def test_selected_n_clusters_matches_reference(kc_reference_dir):
    """A seleção por silhouette converge no n_clusters do TCC (15 para A439). Tolerante a
    pequenas variações de embedding entre versões de SBERT — pina só o n selecionado."""
    pytest.importorskip("sentence_transformers")
    from sentence_transformers import SentenceTransformer

    kc_clusters = _load(kc_reference_dir, "kc_clusters_A439.json")
    expected_n = kc_clusters["n_clusters_selected"]

    kc_names = list(kc_clusters["kc_to_cluster"].keys())
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(kc_names)

    best_n, _scores = choose_kc_group_count(embeddings, candidates=(10, 12, 15))
    assert best_n == expected_n
