# A avaliação em várias seeds, uma execução por seed, com a média e o desvio que o paper reporta.

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.evaluation import seed_evaluation
from ml.evaluation.seed_evaluation import EVALUATION_SEEDS, evaluate_over_seeds
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS

ASSIGNMENT_ID = 439
_FAST_CONFIG = {**CODE_DKT_HYPERPARAMETERS, "epochs": 2}
_BODIES = [
    "public int g0(int a, int b) { int s = a + b; return s; }",
    "public int g1(int a) { for (int i = 0; i < a; i++) { a = a * 2; } return a; }",
    "public boolean g2(int n) { if (n > 0) { return true; } return false; }",
    "public int g3(int n) { while (n > 0) { n = n - 1; } return n; }",
    "public int g4(int[] xs) { int t = 0; for (int x : xs) { t += x; } return t; }",
    "public String g5(boolean b) { return b ? \"yes\" : \"no\"; }",
    "public int g6(int n) { switch (n) { case 0: return 1; default: return n; } }",
    "public int g7(int n) { try { return 10 / n; } catch (Exception e) { return -1; } }",
]


def _frame(all_correct: bool = False, plan=None) -> pd.DataFrame:
    # Oito alunos e três problemas, com acerto e erro na primeira tentativa de cada um
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    plan = plan or [(1, 0.0), (2, 1.0), (1, 1.0), (3, 0.0), (2, 1.0)]
    rows = []
    for s, body in enumerate(_BODIES):
        for step, (problem, score) in enumerate(plan):
            score = 1.0 if all_correct else score
            rows.append({
                "student_id": f"S{s}", "problem_id": problem,
                "progsnap_assignment_id": ASSIGNMENT_ID, "event_type": "Run.Program",
                "submitted_at": base + pd.Timedelta(hours=s, minutes=step),
                "score": score, "is_correct": int(score == 1.0),
                "code_snapshot_id": f"c{s}_{step}", "code": body,
            })
    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")
    return df


def test_the_evaluation_seeds_are_42_to_51():
    assert EVALUATION_SEEDS == tuple(range(42, 52))


def test_one_run_per_seed_with_the_paths_extracted_once(cpu_device, monkeypatch):
    extractions, training_seeds = [], []
    real_extract = seed_evaluation.extract_ast_paths_for_snapshots
    real_train = seed_evaluation.train_and_evaluate

    def counting_extract(*args, **kwargs):
        extractions.append(1)
        return real_extract(*args, **kwargs)

    def recording_train(*args, config, **kwargs):
        training_seeds.append(config["seed"])
        return real_train(*args, config=config, **kwargs)

    monkeypatch.setattr(seed_evaluation, "extract_ast_paths_for_snapshots", counting_extract)
    monkeypatch.setattr(seed_evaluation, "train_and_evaluate", recording_train)

    result = evaluate_over_seeds(
        _frame(), _FAST_CONFIG, progsnap_assignment_id=ASSIGNMENT_ID, device=cpu_device,
        seeds=(42, 43),
    )

    assert extractions == [1]
    assert training_seeds == [42, 43]
    assert list(result.first_attempt_auc_by_seed) == list(result.all_attempts_auc_by_seed) == [42, 43]
    first = list(result.first_attempt_auc_by_seed.values())
    overall = list(result.all_attempts_auc_by_seed.values())
    # O desvio é o amostral, como o TCC 1 calculou o 1,34 das dez seeds
    assert result.first_attempt_auc_mean == pytest.approx(np.mean(first))
    assert result.first_attempt_auc_std == pytest.approx(np.std(first, ddof=1))
    assert result.all_attempts_auc_mean == pytest.approx(np.mean(overall))
    assert result.all_attempts_auc_std == pytest.approx(np.std(overall, ddof=1))


def test_an_undefined_auc_fails_with_the_seed_in_the_message(cpu_device):
    # Todo mundo acerta, então o teste tem uma classe só e o AUC não existe
    with pytest.raises(ValueError, match=r"seed 42.*AUC indefinido"):
        evaluate_over_seeds(
            _frame(all_correct=True), _FAST_CONFIG, progsnap_assignment_id=ASSIGNMENT_ID,
            device=cpu_device, seeds=(42,),
        )


def test_an_undefined_first_attempt_auc_fails_even_with_the_overall_defined(cpu_device):
    # Todos acertam de primeira e erram depois, então só a métrica primária fica sem as duas classes
    plan = [(1, 1.0), (1, 0.0), (2, 1.0), (2, 0.0), (3, 1.0)]
    with pytest.raises(ValueError, match=r"seed 42.*AUC indefinido"):
        evaluate_over_seeds(
            _frame(plan=plan), _FAST_CONFIG, progsnap_assignment_id=ASSIGNMENT_ID,
            device=cpu_device, seeds=(42,),
        )
