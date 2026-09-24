# Modelos treinados em disco (data/<turma>/models/<assignment_id>/v<K>/), cada versão write-once.

from __future__ import annotations

import hashlib
import json
import pickle
import shutil
import sqlite3
from pathlib import Path

import torch

from api.model_training.domain.value_objects.training_outcome import TrainingOutcome
from api.model_training.domain.entities.trained_model_entity import TrainedModel
from api.model_training.domain.value_objects.training_dataset import TrainingDataset
from api.model_training.infrastructure.implementations import model_provenance
from api.model_training.infrastructure.repositories.sqlite_trained_model_repository import (
    SqliteTrainedModelRepository,
)
from api.shared.application.services.clock import utc_now_iso
from api.shared.infrastructure.filesystem import data_layout
from api.shared.infrastructure.filesystem.confined_path import ConfinedPath
from api.shared.infrastructure.database.sqlite_connection import transaction
from ml.code_dkt.model import CodeDKTModel


# Os arquivos de cada versão sob `base_path` (o models/ de uma turma).
class ModelVersionFiles:
    def __init__(self, base_path: str | Path) -> None:
        self._base = Path(base_path)

    def version_dir(self, assignment_id: int, version_number: int) -> Path:
        # Componentes de ids inteiros internos (nunca de nomes de upload), confinados sob a base.
        vdir = self._base / str(int(assignment_id)) / f"v{int(version_number)}"
        return Path(ConfinedPath(vdir, root=self._base))

    def write(
        self,
        assignment_id: int,
        version_number: int,
        model: torch.nn.Module,
        vocab: dict,
        config: dict,
    ) -> dict:
        # Grava state_dict + vocab.pkl + config.json em v<N> write-once (mkdir sem exist_ok).
        vdir = self.version_dir(assignment_id, version_number)
        # parents=True cria a árvore-pai que falte; sem exist_ok, v<N> é write-once.
        vdir.mkdir(parents=True)

        weights_path = vdir / "model.pt"
        vocab_path = vdir / "vocab.pkl"
        config_path = vdir / "config.json"

        # Contrato de reload, input_dim=2M != output_dim=M no CodeDKTModel real; gravados separados.
        input_dim = int(model.input_dim)
        output_dim = int(model.fc.out_features)

        torch.save(model.state_dict(), weights_path)  # só os pesos, não o nn.Module
        with open(vocab_path, "wb") as f:
            pickle.dump(vocab, f)
        # meta carrega tudo pro reload (config, input/output dim, node/path count).
        meta = {
            **dict(config),
            "input_dim": input_dim,
            "output_dim": output_dim,
            "n_problems": output_dim,
            "node_count": vocab["node_count"],
            "path_count": vocab["path_count"],
        }
        with open(config_path, "w") as f:
            json.dump(meta, f, sort_keys=True)

        h = hashlib.sha256()
        for p in (weights_path, vocab_path, config_path):
            h.update(p.read_bytes())
        return {"dir": str(vdir), "content_hash": h.hexdigest()}

    def read(self, vdir: str) -> tuple[CodeDKTModel, dict, dict]:
        # vocab.pkl usa pickle irrestrito; artifact_dir adulterado seria RCE, daí resolve-e-confere
        path = Path(ConfinedPath(vdir, root=self._base))
        meta = json.loads((path / "config.json").read_text())
        with open(path / "vocab.pkl", "rb") as f:
            vocab = pickle.load(f)
        # Args de construção saem do meta (determinístico); input_dim(2M) e output_dim(M) diferem.
        model = CodeDKTModel(
            input_dim=meta["input_dim"],
            hidden_dim=meta["hidden_dim"],
            output_dim=meta["output_dim"],
            node_count=meta["node_count"],
            path_count=meta["path_count"],
            dropout=meta["dropout"],
            R=meta["R"],
            node_embed_dim=meta["node_embed_dim"],
            path_embed_dim=meta["path_embed_dim"],
        )
        # weights_only=True restringe a tensores, sem pickle irrestrito; state_dict só usa tensores.
        model.load_state_dict(
            torch.load(path / "model.pt", map_location="cpu", weights_only=True)
        )
        model.eval()
        return model, vocab, meta


# ITrainedModelStore, arquivos da versão + a linha em model_artifact.
class TrainedModelFileStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._models = SqliteTrainedModelRepository(conn)

    def save(self, dataset: TrainingDataset, assignment_id: int, outcome: TrainingOutcome) -> int:
        # Arquivos fora da transação; falha no INSERT apaga o dir recém-escrito e libera o número.
        files = ModelVersionFiles(data_layout.trained_models_dir(dataset.classroom_id))
        version_number = self._models.next_version_number(assignment_id)
        written = files.write(
            assignment_id, version_number, outcome.model, outcome.vocab, outcome.hyperparameters
        )
        try:
            with transaction(self._conn):
                return self._models.add(
                    TrainedModel(
                        id=None,
                        assignment_id=assignment_id,
                        version_number=version_number,
                        content_hash=written["content_hash"],
                        model_dir=written["dir"],
                        created_at=utc_now_iso(),
                        first_attempt_auc=outcome.first_attempt_auc,
                        git_commit=model_provenance.git_commit(Path.cwd()),
                        data_hash=model_provenance.dataset_hash(dataset.events),
                    )
                )
        except BaseException:
            shutil.rmtree(written["dir"], ignore_errors=True)
            raise

    def load(self, trained_model: TrainedModel, classroom_id: int):
        # (modelo, vocab, meta) de uma versão, confinada ao models/ da turma.
        return ModelVersionFiles(data_layout.trained_models_dir(classroom_id)).read(
            trained_model.model_dir
        )
