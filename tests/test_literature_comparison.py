# O Code-DKT do app ao lado das Tabelas 1 e 2 de Shi et al. (2022), sem asserção contra elas.

# Fora da suíte padrão, roda com -m literature -s, e falha só por erro ou por AUC indefinido.

# Cada exercício grava o AUC de cada seed no arquivo de resultados, que fica versionado.

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
import torch

from ml.code_dkt.student_split import split_students_into_train_and_test
from ml.evaluation.seed_evaluation import EVALUATION_SEEDS, evaluate_over_seeds
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS

# O A1 é o 439 pela Tabela 3 do paper e pelo repositório, e o A2 a A5 seguem a ordem dos ids
PAPER_ASSIGNMENTS = {439: "A1", 487: "A2", 492: "A3", 494: "A4", 502: "A5"}
# A Tabela 1, o AUC geral do Code-DKT em cada exercício, em porcentagem
PAPER_ALL_ATTEMPTS_AUC = {"A1": 74.31, "A2": 76.56, "A3": 80.40, "A4": 72.75, "A5": 79.14}
# A Tabela 2, a média e o desvio do Code-DKT no A1, em porcentagem
PAPER_A1_MEAN_AND_STD = {"first_attempt": [75.74, 0.69], "all_attempts": [74.31, 0.90]}

RESULTS_PATH = (
    Path(__file__).resolve().parents[1] / "docs" / "results" / "code_dkt_literature_comparison.json"
)

_rows: list[str] = []


def _percent(mean: float, std: float) -> str:
    return f"{100 * mean:.2f} ± {100 * std:.2f}"


def _print_table(rows: list[str]) -> None:
    header = "exercício | 1ª tentativa no app | geral no app | geral no paper (Tabela 1)"
    print("\n[literature] " + header + "\n" + "\n".join(f"[literature] {r}" for r in rows))
    # A Tabela 2 só tem o A1, e é a única do paper com a primeira tentativa e o desvio
    first, overall = PAPER_A1_MEAN_AND_STD["first_attempt"], PAPER_A1_MEAN_AND_STD["all_attempts"]
    print(
        f"[literature] Tabela 2 do paper, só no A1, primeira tentativa {_percent_pair(first)} "
        f"e geral {_percent_pair(overall)}"
    )
    print(f"[literature] resultados em {RESULTS_PATH}")


def _percent_pair(mean_and_std: list[float]) -> str:
    return f"{mean_and_std[0]:.2f} ± {mean_and_std[1]:.2f}"


@pytest.fixture(scope="module", autouse=True)
def print_the_comparison_table():
    yield
    if _rows:
        _print_table(_rows)


def _save(progsnap_assignment_id: int, record: dict) -> None:
    # Junta ao arquivo que já existe, para rodar um exercício sozinho sem apagar os outros
    results = json.loads(RESULTS_PATH.read_text()) if RESULTS_PATH.exists() else {}
    results["paper"] = {
        "assignments": {str(k): v for k, v in PAPER_ASSIGNMENTS.items()},
        "table_1_all_attempts_auc_percent": PAPER_ALL_ATTEMPTS_AUC,
        "table_2_a1_mean_and_std_percent": PAPER_A1_MEAN_AND_STD,
    }
    results.setdefault("assignments", {})[str(progsnap_assignment_id)] = record
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


@pytest.mark.literature
@pytest.mark.parametrize("progsnap_assignment_id", sorted(PAPER_ASSIGNMENTS))
def test_literature_comparison(csedm_main_table, progsnap_assignment_id) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_df, test_df = split_students_into_train_and_test(
        csedm_main_table, progsnap_assignment_id=progsnap_assignment_id
    )

    started = time.time()
    evaluation = evaluate_over_seeds(
        csedm_main_table, CODE_DKT_HYPERPARAMETERS,
        progsnap_assignment_id=progsnap_assignment_id, device=device,
    )
    paper_name = PAPER_ASSIGNMENTS[progsnap_assignment_id]
    _save(progsnap_assignment_id, {
        "paper_name": paper_name,
        "seeds": list(EVALUATION_SEEDS),
        "n_students": int(train_df["student_id"].nunique() + test_df["student_id"].nunique()),
        "n_test_students": int(test_df["student_id"].nunique()),
        "first_attempt_auc_by_seed": {str(s): a for s, a in evaluation.first_attempt_auc_by_seed.items()},
        "all_attempts_auc_by_seed": {str(s): a for s, a in evaluation.all_attempts_auc_by_seed.items()},
        "first_attempt_auc_mean": evaluation.first_attempt_auc_mean,
        "first_attempt_auc_std": evaluation.first_attempt_auc_std,
        "all_attempts_auc_mean": evaluation.all_attempts_auc_mean,
        "all_attempts_auc_std": evaluation.all_attempts_auc_std,
        "hyperparameters": dict(CODE_DKT_HYPERPARAMETERS),
        "torch": torch.__version__,
        "device": torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu",
        "seconds": round(time.time() - started, 1),
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    _rows.append(
        f"A{progsnap_assignment_id} ({paper_name}) | "
        f"{_percent(evaluation.first_attempt_auc_mean, evaluation.first_attempt_auc_std)} | "
        f"{_percent(evaluation.all_attempts_auc_mean, evaluation.all_attempts_auc_std)} | "
        f"{PAPER_ALL_ATTEMPTS_AUC[paper_name]:.2f}"
    )
