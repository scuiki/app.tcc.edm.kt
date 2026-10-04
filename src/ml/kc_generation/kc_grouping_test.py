# O número de grupos pela proporção do paper e o agrupamento dos nomes de KC.

from __future__ import annotations

import numpy as np
import pytest

from ml.kc_generation.kc_grouping import group_similar_kcs, kc_group_count


@pytest.mark.parametrize(
    ("n_names", "n_groups"), [(1, 1), (2, 1), (10, 5), (52, 25), (103, 50)]
)
def test_the_group_count_is_the_proportion_of_the_paper(n_names, n_groups):
    # 103 nomes dão os 50 grupos do nível médio da CodeWorkout, e nunca sai menos de um grupo
    assert kc_group_count(n_names) == n_groups


def test_a_single_name_is_its_own_group_without_the_hac():
    assert group_similar_kcs(np.array([[1.0, 0.0]]), 1).tolist() == [0]


def test_the_names_are_grouped_by_the_cosine_distance():
    # Dois pares de vetores em direções quase iguais, e a norma não muda o grupo
    embeddings = np.array([[1.0, 0.0], [10.0, 0.5], [0.0, 1.0], [0.4, 8.0]])
    labels = group_similar_kcs(embeddings, 2)
    assert labels[0] == labels[1] and labels[2] == labels[3] and labels[0] != labels[2]


def test_the_hac_uses_the_average_linkage_on_the_cosine_distance():
    # Com estes ângulos e normas, a ligação média, a completa, a simples e a euclidiana divergem
    angles = np.deg2rad([30, 45, 12, 60, 20])
    norms = np.array([1, 5, 5, 1, 2])
    embeddings = norms[:, None] * np.column_stack([np.cos(angles), np.sin(angles)])
    labels = group_similar_kcs(embeddings, 2)
    groups = {frozenset(np.flatnonzero(labels == g).tolist()) for g in set(labels.tolist())}
    assert groups == {frozenset({0, 2, 4}), frozenset({1, 3})}


def test_the_group_labels_start_at_zero():
    embeddings = np.array([[1.0, 0.0], [10.0, 0.5], [0.0, 1.0], [0.4, 8.0]])
    assert sorted(set(group_similar_kcs(embeddings, 2).tolist())) == [0, 1]
