# ICodeDktTrainer sobre o ml/; hiperparâmetros e função de treino entram pelo construtor (testável).

from __future__ import annotations

from typing import Callable, Mapping

import torch

from api.model_training.domain.value_objects.training_outcome import TrainingOutcome
from api.model_training.domain.value_objects.training_dataset import TrainingDataset
from api.model_training.infrastructure.implementations.ast_path_cache import (
    load_or_extract_ast_paths,
)
from api.model_training.infrastructure.implementations.java_parse_rate import (
    compute_java_parse_rate,
)
from ml.code_dkt.student_split import split_students_into_train_and_test
from ml.code_dkt.train_and_evaluate import code_by_snapshot_id, train_and_evaluate
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS
from ml.reproducibility.random_seed import seed_all_random_generators


class MlCodeDktTrainer:
    def __init__(
        self,
        hyperparameters: Mapping = CODE_DKT_HYPERPARAMETERS,
        train: Callable[..., dict] = train_and_evaluate,
    ) -> None:
        self._hyperparameters = dict(hyperparameters)
        self._train = train

    @property
    def total_epochs(self) -> int:
        return self._hyperparameters["epochs"]

    def train(
        self, dataset: TrainingDataset, on_epoch: Callable[[int, float], None]
    ) -> TrainingOutcome:
        config = dict(self._hyperparameters)
        train_df, test_df = split_students_into_train_and_test(dataset.events)

        # Aquece o cache de paths (reaproveitado no próximo treino/inferência); parse rate sai daqui
        code_by_snapshot = code_by_snapshot_id(dataset.events)
        load_or_extract_ast_paths(
            dataset.classroom_slug, list(code_by_snapshot.keys()), code_by_snapshot, config
        )
        java_parse_rate = compute_java_parse_rate(list(code_by_snapshot.values()), config)

        # Não estrito na GPU, o treino confia na banda de ±3pp em vez do determinismo bit a bit.
        seed_all_random_generators(config["seed"], strict=False)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        result = self._train(
            train_df,
            config=config,
            test_df=test_df,
            # int, não o value object (o ml/ compara com a coluna; VO casaria com zero linhas).
            progsnap_assignment_id=dataset.progsnap_assignment_id.value,
            device=device,
            on_epoch=on_epoch,
            n_workers=None,
        )
        return TrainingOutcome(
            model=result["model"],
            vocab=result["vocab"],
            hyperparameters=config,
            first_attempt_auc=result["first_attempt_auc"],
            java_parse_rate=java_parse_rate,
        )
