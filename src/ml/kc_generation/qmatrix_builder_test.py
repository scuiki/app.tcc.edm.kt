# build_qmatrix reproduz a Q-matrix do TCC 1 (A439) célula a célula; LLM nunca é chamado aqui.

from __future__ import annotations

import json

from ml.kc_generation.qmatrix_builder import build_qmatrix


def _load(kc_reference_dir, name):
    return json.loads((kc_reference_dir / name).read_text())


def test_build_qmatrix_reproduces_reference(kc_reference_dir):
    # Reproduz qmatrix_A439.csv célula-a-célula, replay determinístico a partir do cru cacheado.
    import pandas as pd

    kc_raw = _load(kc_reference_dir, "kc_raw_A439.json")
    kc_clusters = _load(kc_reference_dir, "kc_clusters_A439.json")
    # O CSV é o artefato do TCC 1 e guarda o índice com o nome do ProgSnap2.
    reference = pd.read_csv(kc_reference_dir / "qmatrix_A439.csv", index_col="ProblemID")
    reference.index.name = "problem_id"

    # Os problem_ids da referência (o índice do CSV) na mesma ordem.
    problem_ids = [str(p) for p in reference.index.tolist()]
    produced = build_qmatrix(problem_ids, kc_raw, kc_clusters)

    # Mesma forma (n_problemas × n_clusters) e mesmos valores binários.
    assert list(produced.columns) == list(reference.columns)
    assert produced.shape == reference.shape
    # Comparação célula-a-célula (alinha por reset de índice; valores 0/1).
    assert produced.to_numpy().tolist() == reference.to_numpy().tolist()


def test_zero_kc_problem_guard(kc_reference_dir):
    # Guarda 0-KC, problema sem KC mapeado fica com a linha toda zero; não inventamos vínculo.
    kc_clusters = _load(kc_reference_dir, "kc_clusters_A439.json")
    kc_raw = {}  # nenhum KC para nenhum problema

    produced = build_qmatrix(["999"], kc_raw, kc_clusters)
    # Sem KCs, a linha do problema é inteiramente 0 (a falha-dura é decisão da validação).
    assert produced.loc["999"].sum() == 0
