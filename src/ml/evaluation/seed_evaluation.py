# Treina e avalia um exercício uma vez por seed, para a média e o desvio que o paper reporta.

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd
import torch

from ml.code_dkt.ast_paths import extract_ast_paths_for_snapshots
from ml.code_dkt.student_split import split_students_into_train_and_test
from ml.code_dkt.train_and_evaluate import code_by_snapshot_id, train_and_evaluate
from ml.reproducibility.random_seed import seed_all_random_generators

# Uma execução por seed, como o TCC 1, para cada uma poder ser refeita sozinha
EVALUATION_SEEDS = tuple(range(42, 52))


@dataclass(frozen=True)
class SeedEvaluation:
    first_attempt_auc_by_seed: dict[int, float]
    all_attempts_auc_by_seed: dict[int, float]

    @property
    def first_attempt_auc_mean(self) -> float:
        return float(np.mean(list(self.first_attempt_auc_by_seed.values())))

    @property
    def first_attempt_auc_std(self) -> float:
        # Desvio amostral, como o TCC 1 calculou o das dez seeds
        return float(np.std(list(self.first_attempt_auc_by_seed.values()), ddof=1))

    @property
    def all_attempts_auc_mean(self) -> float:
        return float(np.mean(list(self.all_attempts_auc_by_seed.values())))

    @property
    def all_attempts_auc_std(self) -> float:
        return float(np.std(list(self.all_attempts_auc_by_seed.values()), ddof=1))


def evaluate_over_seeds(
    df: pd.DataFrame,
    config: Mapping,
    *,
    progsnap_assignment_id: int,
    device: torch.device | None = None,
    seeds: tuple[int, ...] = EVALUATION_SEEDS,
) -> SeedEvaluation:
    # A partição e os paths saem uma vez, e entre as execuções só muda a seed do treino
    train_df, test_df = split_students_into_train_and_test(
        df, progsnap_assignment_id=progsnap_assignment_id
    )
    code_by_snapshot = code_by_snapshot_id(pd.concat([train_df, test_df], ignore_index=True))
    ast_paths_by_snapshot = extract_ast_paths_for_snapshots(
        sorted(code_by_snapshot), code_by_snapshot,
        max_path_length=config["max_path_length"],
        max_path_width=config["max_path_width"],
    )

    first_attempt, all_attempts = {}, {}
    for seed in seeds:
        seed_all_random_generators(seed, strict=False)
        result = train_and_evaluate(
            train_df, config={**config, "seed": seed}, test_df=test_df,
            progsnap_assignment_id=progsnap_assignment_id,
            ast_paths_by_snapshot=ast_paths_by_snapshot, device=device,
        )
        if not (np.isfinite(result["first_attempt_auc"]) and np.isfinite(result["all_attempts_auc"])):
            raise ValueError(
                f"A seed {seed} deu AUC indefinido no exercício {progsnap_assignment_id}, porque "
                "os acertos do teste têm uma classe só, e a média das seeds não teria sentido."
            )
        first_attempt[seed] = result["first_attempt_auc"]
        all_attempts[seed] = result["all_attempts_auc"]
    return SeedEvaluation(first_attempt, all_attempts)
