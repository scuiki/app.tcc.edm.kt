# O Code-DKT com as tentativas na ordem do arquivo, como o repositório oficial, ao lado do paper.

# Fora da suíte padrão, roda com -m ablation -s, e falha só por erro ou por AUC indefinido.

# A ordem do tempo vem dos resultados da comparação com o paper, que se repetem bit a bit.

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
import torch

from ml.code_dkt.student_sequences import build_student_sequences
from ml.code_dkt.student_split import split_students_into_train_and_test
from ml.evaluation.seed_evaluation import EVALUATION_SEEDS, evaluate_over_seeds
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS
from tests.test_literature_comparison import (
    PAPER_A1_MEAN_AND_STD,
    PAPER_ALL_ATTEMPTS_AUC,
    PAPER_ASSIGNMENTS,
    RESULTS_PATH as LITERATURE_RESULTS_PATH,
)

RESULTS_PATH = LITERATURE_RESULTS_PATH.parent / "code_dkt_order_ablation.json"

_rows: list[str] = []


def _percent(mean: float, std: float) -> str:
    return f"{100 * mean:.2f} ± {100 * std:.2f}"


@pytest.fixture(scope="module", autouse=True)
def print_the_ablation_table():
    yield
    if not _rows:
        return
    header = "exercício | ordem | 1ª tentativa | geral | geral no paper (Tabela 1)"
    print("\n[ablation] " + header + "\n" + "\n".join(f"[ablation] {r}" for r in _rows))
    first, overall = PAPER_A1_MEAN_AND_STD["first_attempt"], PAPER_A1_MEAN_AND_STD["all_attempts"]
    print(
        f"[ablation] Tabela 2 do paper, só no A1, primeira tentativa {first[0]:.2f} ± {first[1]:.2f} "
        f"e geral {overall[0]:.2f} ± {overall[1]:.2f}"
    )
    print(f"[ablation] resultados em {RESULTS_PATH}")


def _count_first_attempts(test_df, progsnap_assignment_id: int, attempt_order: str) -> int:
    # As primeiras tentativas que o AUC conta, nas últimas 50 e sem a primeira execução do aluno
    total = 0
    for seq in build_student_sequences(test_df, progsnap_assignment_id, attempt_order):
        window = seq["events"].iloc[-CODE_DKT_HYPERPARAMETERS["max_len"]:]
        total += int(window["is_first_attempt"].iloc[1:].sum())
    return total


def _save(progsnap_assignment_id: int, record: dict) -> None:
    # Junta ao arquivo que já existe, para rodar um exercício sozinho sem apagar os outros
    results = json.loads(RESULTS_PATH.read_text()) if RESULTS_PATH.exists() else {}
    results.setdefault("assignments", {})[str(progsnap_assignment_id)] = record
    RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


@pytest.mark.ablation
@pytest.mark.parametrize("progsnap_assignment_id", sorted(PAPER_ASSIGNMENTS))
def test_file_order_ablation(csedm_main_table, progsnap_assignment_id) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _train_df, test_df = split_students_into_train_and_test(
        csedm_main_table, progsnap_assignment_id=progsnap_assignment_id
    )
    time_order = json.loads(LITERATURE_RESULTS_PATH.read_text())["assignments"][
        str(progsnap_assignment_id)
    ]

    started = time.time()
    evaluation = evaluate_over_seeds(
        csedm_main_table, {**CODE_DKT_HYPERPARAMETERS, "attempt_order": "file"},
        progsnap_assignment_id=progsnap_assignment_id, device=device,
    )
    paper_name = PAPER_ASSIGNMENTS[progsnap_assignment_id]
    _save(progsnap_assignment_id, {
        "paper_name": paper_name,
        "attempt_order": "file",
        "seeds": list(EVALUATION_SEEDS),
        "n_first_attempts_in_test": {
            order: _count_first_attempts(test_df, progsnap_assignment_id, order)
            for order in ("time", "file")
        },
        "first_attempt_auc_by_seed": {str(s): a for s, a in evaluation.first_attempt_auc_by_seed.items()},
        "all_attempts_auc_by_seed": {str(s): a for s, a in evaluation.all_attempts_auc_by_seed.items()},
        "first_attempt_auc_mean": evaluation.first_attempt_auc_mean,
        "first_attempt_auc_std": evaluation.first_attempt_auc_std,
        "all_attempts_auc_mean": evaluation.all_attempts_auc_mean,
        "all_attempts_auc_std": evaluation.all_attempts_auc_std,
        "torch": torch.__version__,
        "device": torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu",
        "seconds": round(time.time() - started, 1),
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    paper = f"{PAPER_ALL_ATTEMPTS_AUC[paper_name]:.2f}"
    name = f"A{progsnap_assignment_id} ({paper_name})"
    _rows.append(
        f"{name} | tempo, o app | "
        f"{_percent(time_order['first_attempt_auc_mean'], time_order['first_attempt_auc_std'])} | "
        f"{_percent(time_order['all_attempts_auc_mean'], time_order['all_attempts_auc_std'])} | {paper}"
    )
    _rows.append(
        f"{name} | arquivo | "
        f"{_percent(evaluation.first_attempt_auc_mean, evaluation.first_attempt_auc_std)} | "
        f"{_percent(evaluation.all_attempts_auc_mean, evaluation.all_attempts_auc_std)} | {paper}"
    )
