"""RED — replay de referência do pipeline KCGen-KT puro (KC-01, KC-04).

Reproduz a Q-matrix e o clustering do TCC 1 (A439) a partir do CRU cacheado, com o LLM
SEMPRE mockado (carregamos `kc_raw_A439.json` como se fosse o cache de geração) — nenhum
teste chama `claude` real nem gasta cota. O `build_qmatrix` é função pura DataFrame→DataFrame
(determinística dado kc_raw + kc_clusters): seu output deve bater célula-a-célula com
`qmatrix_A439.csv`. A seleção de n_clusters por silhouette deve bater com
`kc_clusters_A439.json` (n=15). Assertions sensíveis a embeddings (que variam entre versões
do SBERT) ficam tolerantes; o n_clusters selecionado é pinado. Também pina a guarda 0-KC (D-04).

Wave 0: `edmkt_core.kc.qmatrix` / `edmkt_core.kc.clustering` ainda não existem → FALHA RED.
"""

from __future__ import annotations

import json

import pytest

# RED: o core puro do KC ainda não existe (gate da Wave 1/2).
from edmkt_core.kc.clustering import select_best_n_clusters  # noqa: E402
from edmkt_core.kc.qmatrix import build_qmatrix  # noqa: E402


def _load(kc_reference_dir, name):
    return json.loads((kc_reference_dir / name).read_text())


def test_build_qmatrix_reproduces_reference(kc_reference_dir):
    """build_qmatrix(problem_ids, kc_raw, kc_clusters) reproduz qmatrix_A439.csv célula-a-célula
    (replay determinístico a partir do cru cacheado — o objeto científico reproduzível, D-03)."""
    import pandas as pd

    kc_raw = _load(kc_reference_dir, "kc_raw_A439.json")
    kc_clusters = _load(kc_reference_dir, "kc_clusters_A439.json")
    reference = pd.read_csv(kc_reference_dir / "qmatrix_A439.csv", index_col="ProblemID")

    # Os problem_ids da referência (o índice do CSV) na mesma ordem.
    problem_ids = [str(p) for p in reference.index.tolist()]
    produced = build_qmatrix(problem_ids, kc_raw, kc_clusters)

    # Mesma forma (n_problemas × n_clusters) e mesmos valores binários.
    assert list(produced.columns) == list(reference.columns)
    assert produced.shape == reference.shape
    # Comparação célula-a-célula (alinha por reset de índice; valores 0/1).
    assert produced.to_numpy().tolist() == reference.to_numpy().tolist()


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

    best_n, _scores = select_best_n_clusters(embeddings, candidates=(10, 12, 15))
    assert best_n == expected_n


def test_zero_kc_problem_guard(kc_reference_dir):
    """Guarda 0-KC (D-04): um problema sem nenhum KC mapeado fica com a linha toda zero, o que
    a validação a jusante trata como falha-dura. Aqui pinamos que build_qmatrix não inventa
    bindings para um problema ausente do kc_raw (linha toda 0)."""
    kc_clusters = _load(kc_reference_dir, "kc_clusters_A439.json")
    kc_raw = {}  # nenhum KC para nenhum problema

    produced = build_qmatrix(["999"], kc_raw, kc_clusters)
    # Sem KCs, a linha do problema é inteiramente 0 (a falha-dura é decisão da validação).
    assert produced.loc["999"].sum() == 0
