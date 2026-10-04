# A amostragem das soluções corretas, com vetores falsos no lugar do CodeBERT.

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering

from ml.kc_generation.solution_sampling import SOLUTIONS_PER_PROBLEM, select_sample_solutions


def _vector(code: str) -> np.ndarray:
    # A estratégia é o número antes do ponto, e as variantes de uma estratégia ficam quase iguais
    strategy, variant = code.split(".")
    vector = np.zeros(16)
    vector[int(strategy)] = 1.0
    vector[15] = 0.01 * int(variant)
    return vector / np.linalg.norm(vector)


class _Embed:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, codes: list[str]) -> np.ndarray:
        self.calls.append(list(codes))
        return np.stack([_vector(code) for code in codes])


def _runs(
    codes: list[str], submission_ids: list[int] | None = None, same_instant: bool = False
) -> pd.DataFrame:
    base = pd.Timestamp("2026-01-01T00:00:00Z")
    return pd.DataFrame(
        {
            "submission_id": submission_ids or list(range(1, len(codes) + 1)),
            "student_id": [f"S{i}" for i in range(len(codes))],
            "problem_id": [1] * len(codes),
            "code_snapshot_id": [f"c{i}" for i in range(len(codes))],
            "code": codes,
            "submitted_at": [
                base if same_instant else base + pd.Timedelta(minutes=i) for i in range(len(codes))
            ],
        }
    )


def _embed_angles(codes: list[str]) -> np.ndarray:
    # Cada código é um ângulo em graus, e o vetor é o ponto do círculo unitário nesse ângulo
    radians = np.radians([float(code) for code in codes])
    return np.stack([np.cos(radians), np.sin(radians)], axis=1)


# Os ângulos e o grupo de cada um pela ligação média com a distância cosseno, em 4 grupos
_GROUP_OF_ANGLE = {0: 0, 10: 0, 25: 1, 60: 2, 70: 2, 85: 2, 145: 3, 165: 3}


def _strategies(samples: list[dict]) -> list[int]:
    return sorted(int(sample["code"].split(".")[0]) for sample in samples)


def test_five_strategies_give_one_solution_each():
    codes = [f"{strategy}.{variant}" for strategy in range(5) for variant in (1, 2, 3)]
    samples = select_sample_solutions(_runs(codes), _Embed())
    assert len(samples) == SOLUTIONS_PER_PROBLEM
    assert _strategies(samples) == [0, 1, 2, 3, 4]


def test_fewer_distinct_solutions_than_five_send_each_one_once():
    # Três soluções distintas, mandadas várias vezes, viram três grupos sem repetir o código
    samples = select_sample_solutions(_runs(["0.1", "0.1", "1.1", "1.1", "1.1", "2.1"]), _Embed())
    assert sorted(sample["code"] for sample in samples) == ["0.1", "1.1", "2.1"]


def test_identical_codes_are_embedded_once():
    embed = _Embed()
    select_sample_solutions(_runs(["0.1", "0.1", "1.1", "2.1"]), embed)
    assert embed.calls == [["0.1", "1.1", "2.1"]]


def test_a_single_distinct_solution_is_the_whole_sample_without_the_codebert():
    embed = _Embed()
    samples = select_sample_solutions(_runs(["3.1", "3.1"]), embed)
    assert len(samples) == 1 and samples[0]["code"] == "3.1"
    assert embed.calls == []


def test_no_correct_run_gives_no_sample():
    assert select_sample_solutions(_runs([]), _Embed()) == []


def test_the_sample_follows_the_time_and_not_the_row_order():
    runs = _runs([f"{strategy}.{variant}" for strategy in range(5) for variant in (1, 2, 3)])
    shuffled = runs.sample(frac=1.0, random_state=7)
    first = select_sample_solutions(runs, _Embed())
    second = select_sample_solutions(shuffled, _Embed())
    assert [s["submission_id"] for s in first] == [s["submission_id"] for s in second]


def test_the_draw_inside_each_group_is_seeded():
    runs = _runs([f"{strategy}.{variant}" for strategy in range(5) for variant in (1, 2, 3)])
    draws = {
        tuple(s["submission_id"] for s in select_sample_solutions(runs, _Embed())) for _ in range(3)
    }
    assert len(draws) == 1


def test_the_groups_come_from_the_average_linkage_on_the_cosine_distance():
    # As outras ligações e a distância euclidiana juntam o 25 ao 0 e ao 10, e nenhum sorteio passa
    samples = select_sample_solutions(_runs([str(a) for a in _GROUP_OF_ANGLE]), _embed_angles, n=4)
    assert sorted(_GROUP_OF_ANGLE[int(sample["code"])] for sample in samples) == [0, 1, 2, 3]


def test_the_samples_follow_the_order_of_the_group_labels():
    # O repositório percorre os grupos pelo rótulo, e é nessa ordem que as soluções vão ao prompt
    codes = [str(angle) for angle in _GROUP_OF_ANGLE]
    labels = AgglomerativeClustering(n_clusters=4, metric="cosine", linkage="average").fit_predict(
        _embed_angles(codes)
    )
    label_of = dict(zip(codes, labels))
    samples = select_sample_solutions(_runs(codes), _embed_angles, n=4)
    assert [label_of[sample["code"]] for sample in samples] == [0, 1, 2, 3]


def test_runs_at_the_same_instant_are_ordered_by_their_id():
    # No A439 há execuções corretas do mesmo problema com o mesmo horário
    codes = [f"{strategy}.{variant}" for strategy in range(5) for variant in (1, 2, 3)]
    runs = _runs(codes, same_instant=True)
    shuffled = runs.sample(frac=1.0, random_state=3)
    first = select_sample_solutions(runs, _Embed())
    second = select_sample_solutions(shuffled, _Embed())
    assert [s["submission_id"] for s in first] == [s["submission_id"] for s in second]


def test_the_time_and_not_the_id_decides_the_order():
    codes = [f"{strategy}.{variant}" for strategy in range(5) for variant in (1, 2, 3)]
    backward_ids = list(range(len(codes), 0, -1))
    forward = select_sample_solutions(_runs(codes), _Embed())
    backward = select_sample_solutions(_runs(codes, submission_ids=backward_ids), _Embed())
    assert [s["code"] for s in forward] == [s["code"] for s in backward]
