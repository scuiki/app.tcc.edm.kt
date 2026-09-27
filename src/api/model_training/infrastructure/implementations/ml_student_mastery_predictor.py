# Vocabulário SEMPRE recarregado da versão, nunca reconstruído (vazaria a partição de teste).

from __future__ import annotations

from api.model_training.domain.entities.trained_model_entity import TrainedModel
from api.model_training.domain.value_objects.training_dataset import TrainingDataset
from api.model_training.infrastructure.implementations.ast_path_cache import (
    load_or_extract_ast_paths,
)
from api.model_training.infrastructure.implementations.trained_model_file_store import (
    TrainedModelFileStore,
)
from ml.code_dkt.prediction import predict_current_state
from ml.code_dkt.problem_index import build_problem_index
from ml.code_dkt.student_sequences import build_student_sequences
from ml.code_dkt.train_and_evaluate import code_by_snapshot_id, code_snapshot_ids
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS


class MlStudentMasteryPredictor:
    def __init__(self, model_store: TrainedModelFileStore) -> None:
        self._model_store = model_store

    def predict_current_mastery(
        self, trained_model: TrainedModel, dataset: TrainingDataset
    ) -> dict[tuple[str, int], float]:
        # O vetor do último passo de cada aluno; leitura confinada ao models/ da turma
        model, vocab, meta = self._model_store.load(trained_model, dataset.classroom_id)

        # int, não o value object (o ml/ filtra a coluna do DataFrame pelo int).
        sequences = build_student_sequences(dataset.events, dataset.progsnap_assignment_id.value)
        # Parâmetros de extração vêm do meta da versão, completados pelos hiperparâmetros congelados
        ast_paths_by_snapshot = load_or_extract_ast_paths(
            dataset.classroom_id,
            dataset.assignment_id,
            sorted(set(code_snapshot_ids(sequences))),
            code_by_snapshot_id(dataset.events),
            {**CODE_DKT_HYPERPARAMETERS, **meta},
        )
        state = predict_current_state(
            model,
            sequences,
            build_problem_index(sequences),
            vocab,
            ast_paths_by_snapshot,
            max_len=meta.get("max_len", 50),
            R=meta.get("R", 50),
        )
        return {
            (row.student_id, int(row.problem_id)): float(row.predicted_correct_probability)
            for row in state.itertuples(index=False)
        }
