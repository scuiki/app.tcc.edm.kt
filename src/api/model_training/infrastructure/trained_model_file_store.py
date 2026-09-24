"""Os modelos treinados em disco: data/<turma>/models/<assignment_id>/v<K>/.

Cada versão é um diretório write-once com os pesos (model.pt), o vocabulário (vocab.pkl) e tudo que
reconstrói o modelo (config.json). A ordem ao gravar sustenta a consistência: arquivos → linha no
banco → publicação (esta última é do use case). Publicar antes exporia uma versão incompleta.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import shutil
import sqlite3
from pathlib import Path

import torch

from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
from api.model_training.domain.code_dkt_trainer import TrainingOutcome
from api.model_training.domain.trained_model_entity import TrainedModel
from api.model_training.domain.training_dataset import TrainingDataset
from api.model_training.infrastructure import model_provenance
from api.model_training.infrastructure.sqlite_trained_model_repository import (
    SqliteTrainedModelRepository,
)
from api.shared.application.services.clock import utc_now_iso
from api.shared.infrastructure.filesystem import data_layout
from api.shared.infrastructure.filesystem.confined_path import ConfinedPath
from api.shared.infrastructure.database.sqlite_connection import transaction
from ml.code_dkt.model import CodeDKTModel


class ModelVersionFiles:
    """Os arquivos de cada versão sob `base_path` (o models/ de uma turma)."""

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
        """Grava state_dict + vocab.pkl + config.json num v<N> write-once; devolve dir+hash.

        n_problems é derivado do modelo vivo (model.input_dim / model.fc.out_features),
        evitando alterar o ml. O diretório é criado SEM exist_ok: re-gravar uma
        versão existente levanta FileExistsError (write-once)."""
        vdir = self.version_dir(assignment_id, version_number)
        # parents=True cria a árvore-pai que falte (turma/assignment/models) sem falhar se já
        # existe; SEM exist_ok o v<N> final é write-once — FileExistsError se já existir.
        vdir.mkdir(parents=True)

        weights_path = vdir / "model.pt"
        vocab_path = vdir / "vocab.pkl"
        config_path = vdir / "config.json"

        # Contrato de reload: o CodeDKTModel real tem input_dim=2M e output_dim=M
        # — NÃO são iguais (assumir input_dim == output_dim == n_problems
        # causaria size mismatch no modelo de verdade).
        # n_problems = M = output_dim = fc.out_features; input_dim e output_dim são gravados
        # separadamente, derivados do objeto vivo, para reconstruir sem assumir a relação 2M.
        input_dim = int(model.input_dim)
        output_dim = int(model.fc.out_features)

        torch.save(model.state_dict(), weights_path)  # só os pesos, não o nn.Module
        with open(vocab_path, "wb") as f:
            pickle.dump(vocab, f)
        # meta carrega TUDO que reconstrói o modelo no reload: config + input/output
        # dim + node_count/path_count do vocab. n_problems (=output_dim=M) fica explícito como
        # o id de problemas. sort_keys deixa o JSON (e o hash) estável.
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
        """Reconstrói o CodeDKTModel pelos args do meta ANTES do load_state_dict.

        map_location='cpu' (a suíte é CPU-only) e model.eval() (inferência). Devolve
        (model, vocab, meta)."""
        # vdir vem de a linha do modelo (DB-owned), mas o vocab.pkl é lido com
        # pickle.load IRRESTRITO (≠ torch.load weights_only=True do .pt). Um artifact_dir
        # adulterado/fora-da-árvore apontaria a desserialização para um .pkl arbitrário ⇒ RCE.
        # Mesma guarda resolve-depois-confere de version_dir ANTES de abrir o .pkl.
        path = Path(ConfinedPath(vdir, root=self._base))
        meta = json.loads((path / "config.json").read_text())
        with open(path / "vocab.pkl", "rb") as f:
            vocab = pickle.load(f)
        # Todos os args de construção saem do meta — reconstrução determinística.
        # input_dim (2M) e output_dim (M) são distintos no CodeDKTModel real — usar os valores
        # gravados, não assumir input_dim==output_dim.
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
        # weights_only=True restringe a desserialização a tensores (sem pickle irrestrito);
        # o state_dict é dict[str, Tensor], totalmente suportado nesse modo.
        model.load_state_dict(
            torch.load(path / "model.pt", map_location="cpu", weights_only=True)
        )
        model.eval()
        return model, vocab, meta


class TrainedModelFileStore:
    """TrainedModelStore: arquivos da versão + a linha em model_artifact."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._models = SqliteTrainedModelRepository(conn)

    def save(self, dataset: TrainingDataset, assignment_id: int, outcome: TrainingOutcome) -> int:
        """Grava os arquivos e a linha; devolve o id da versão. NÃO publica.

        Os arquivos ficam FORA da transação: dentro dela, uma falha do INSERT desfaria o banco mas
        deixaria o v<K> órfão no disco, e a próxima gravação bateria no mesmo K. Em qualquer falha
        do INSERT, o diretório recém-escrito é apagado e o número da versão fica livre de novo.
        """
        files = ModelVersionFiles(data_layout.trained_models_dir(dataset.classroom_slug))
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
                        data_hash=model_provenance.file_hash(
                            data_layout.cleaned_submissions_path(
                                dataset.classroom_slug, dataset.progsnap_assignment_id
                            )
                        ),
                    )
                )
        except BaseException:
            shutil.rmtree(written["dir"], ignore_errors=True)
            raise

    def load(self, trained_model: TrainedModel, classroom_slug: ClassroomSlug):
        """(modelo, vocab, meta) de uma versão, confinada ao models/ da turma."""
        return ModelVersionFiles(data_layout.trained_models_dir(classroom_slug)).read(
            trained_model.model_dir
        )
