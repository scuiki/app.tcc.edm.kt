# build_qmatrix reproduz a Q-matrix da extração de referência do A439, sem chamar o LLM.

from __future__ import annotations

import json

from ml.kc_generation.qmatrix_builder import build_qmatrix


def _reference(kc_reference_dir) -> dict:
    path = kc_reference_dir / "a439_reference_extraction.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_build_qmatrix_reproduces_the_reference_extraction(kc_reference_dir):
    # Os KCs candidatos e o grupo de cada nome dão de novo os conceitos de cada problema
    reference = _reference(kc_reference_dir)
    problem_ids = sorted(int(p) for p in reference["candidate_kcs"])
    candidates = {int(p): kcs for p, kcs in reference["candidate_kcs"].items()}
    n_groups = len(reference["concepts"])

    qmatrix = build_qmatrix(
        problem_ids,
        candidates,
        {"n_clusters_selected": n_groups, "kc_to_cluster": reference["group_of_name"]},
    )

    assert qmatrix.shape == (len(problem_ids), n_groups)
    assert list(qmatrix.columns) == [f"kc_{g}" for g in range(n_groups)]
    assert list(qmatrix.index) == problem_ids
    produced = {
        p: [g for g in range(n_groups) if qmatrix.loc[p][f"kc_{g}"] == 1] for p in problem_ids
    }
    assert produced == {int(p): groups for p, groups in reference["groups_by_problem"].items()}


def test_zero_kc_problem_guard():
    # Um problema sem KC candidato fica com a linha zerada, e quem recusa é a validação da geração
    produced = build_qmatrix([999], {}, {"n_clusters_selected": 2, "kc_to_cluster": {"loop": 0}})

    assert produced.loc[999].sum() == 0
