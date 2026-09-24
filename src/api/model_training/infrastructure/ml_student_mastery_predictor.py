"""StudentMasteryPredictor sobre o ml/: recarrega a versão, prevê cada tentativa e agrega por KC.

O vocabulário é SEMPRE o recarregado da versão, nunca reconstruído: reconstruí-lo vazaria a
partição de teste. As entradas seguem a mesma montagem do treino (sequências completas → AST
paths → índice de problemas), sobre o mesmo cache de paths em disco que o treino aqueceu.
"""

from __future__ import annotations

import pandas as pd

from api.model_training.domain.trained_model_entity import TrainedModel
from api.model_training.domain.training_dataset import TrainingDataset
from api.model_training.infrastructure.ast_path_cache import load_or_extract_ast_paths
from api.model_training.infrastructure.trained_model_file_store import TrainedModelFileStore
from ml.code_dkt.prediction import predict_code_dkt
from ml.code_dkt.problem_index import build_problem_index
from ml.code_dkt.student_sequences import build_student_sequences
from ml.code_dkt.train_and_evaluate import code_by_snapshot_id, code_snapshot_ids
from ml.mastery.mastery_aggregation import aggregate_student_mastery
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS


class MlStudentMasteryPredictor:
    def __init__(self, model_store: TrainedModelFileStore) -> None:
        self._model_store = model_store

    def predict_mastery(
        self,
        trained_model: TrainedModel,
        dataset: TrainingDataset,
        kcs_by_problem: dict[int, list[int]],
    ) -> dict[tuple[str, int], float]:
        return aggregate_student_mastery(self.predict(trained_model, dataset), kcs_by_problem)

    def predict(self, trained_model: TrainedModel, dataset: TrainingDataset) -> pd.DataFrame:
        """A probabilidade prevista de acerto de cada tentativa (menos a primeira de cada aluno)."""
        # A leitura dos arquivos é confinada ao models/ da turma e desserializa os pesos com
        # weights_only=True.
        model, vocab, meta = self._model_store.load(trained_model, dataset.classroom_slug)

        # int, não o value object: o ml/ filtra a coluna do DataFrame pelo int.
        sequences = build_student_sequences(dataset.events, dataset.progsnap_assignment_id.value)
        # Os parâmetros de extração são os do meta da versão, completados pelos hiperparâmetros
        # congelados (os defaults com que toda versão foi treinada).
        ast_paths_by_snapshot = load_or_extract_ast_paths(
            dataset.classroom_slug,
            sorted(set(code_snapshot_ids(sequences))),
            code_by_snapshot_id(dataset.events),
            {**CODE_DKT_HYPERPARAMETERS, **meta},
        )
        return predict_code_dkt(
            model,
            sequences,
            build_problem_index(sequences),
            vocab,
            ast_paths_by_snapshot,
            max_len=meta.get("max_len", 50),
            R=meta.get("R", 50),
        )
