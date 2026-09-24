"""ArtifactStore: o blob write-once de cada versão de modelo, e seu reload confinado."""

from __future__ import annotations

import hashlib
import json
import pickle
import shutil
import sqlite3
from pathlib import Path
from typing import Optional

import torch

from edmkt_core.models.code_dkt import CodeDKTModel

from edmkt_app.persistence.artifacts.versioning import next_version_number
from edmkt_app.persistence.db import transaction
from edmkt_app.values import ConfinedPath
from edmkt_app.clock import utc_now_iso


class ArtifactStore:
    """Grava/relê versões de modelo write-once sob `base_path` (D-05/D-06).

    save_version escreve um diretório v<N> e devolve dir + content_hash; load_version
    reconstrói o CodeDKTModel pelo contrato de reload; persist amarra a versão monótona ao
    INSERT na mesma transação. O flip do ponteiro é função separada (flip_current), chamada
    DEPOIS que o blob e a linha já existem (ordem load-bearing, Pitfall 2)."""

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)

    def _version_dir(self, assignment_id: int, version_number: int) -> Path:
        # Componentes derivados de IDs inteiros internos (nunca de nomes de upload). Resolve
        # e valida que o diretório fica sob base — defesa contra traversal (RESEARCH §Security).
        #
        # A base JÁ termina em .../<turma_slug>/models (é assim que os dois chamadores a
        # constroem), então aqui não se acrescenta nem a turma nem outro "models": era essa
        # dupla contagem que produzia `data/<turma>/models/1/1/models/v1` (999.1).
        vdir = self._base / str(int(assignment_id)) / f"v{int(version_number)}"
        return Path(ConfinedPath(vdir, root=self._base))

    def save_version(
        self,
        turma_id: int,
        assignment_id: int,
        version_number: int,
        model: torch.nn.Module,
        vocab: dict,
        config: dict,
    ) -> dict:
        """Grava state_dict + vocab.pkl + config.json num v<N> write-once; devolve dir+hash.

        n_problems é derivado do modelo vivo (model.input_dim / model.fc.out_features — Open
        Q1), evitando alterar o edmkt_core. O diretório é criado SEM exist_ok: re-gravar uma
        versão existente levanta FileExistsError (write-once, D-05/D-06)."""
        vdir = self._version_dir(assignment_id, version_number)
        # parents=True cria a árvore-pai que falte (turma/assignment/models) sem falhar se já
        # existe; SEM exist_ok o v<N> final é write-once — FileExistsError se já existir (D-05/D-06).
        vdir.mkdir(parents=True)

        weights_path = vdir / "model.pt"
        vocab_path = vdir / "vocab.pkl"
        config_path = vdir / "config.json"

        # Contrato de reload (Pitfall 1): o CodeDKTModel real tem input_dim=2M e output_dim=M
        # (code_dkt.py:148,150) — NÃO são iguais (o exemplo do RESEARCH que assume
        # input_dim==output_dim==n_problems causaria size mismatch no modelo de verdade).
        # n_problems = M = output_dim = fc.out_features; input_dim e output_dim são gravados
        # separadamente, derivados do objeto vivo, para reconstruir sem assumir a relação 2M.
        input_dim = int(model.input_dim)
        output_dim = int(model.fc.out_features)

        torch.save(model.state_dict(), weights_path)  # só os pesos (não o nn.Module — D-05)
        with open(vocab_path, "wb") as f:
            pickle.dump(vocab, f)
        # meta carrega TUDO que reconstrói o modelo no reload (Pitfall 1): config + input/output
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

    def load_version(self, vdir: str) -> tuple[CodeDKTModel, dict, dict]:
        """Reconstrói o CodeDKTModel pelos args do meta ANTES do load_state_dict (Pitfall 1).

        map_location='cpu' (a suíte é CPU-only) e model.eval() (inferência). Devolve
        (model, vocab, meta)."""
        # CR-02: vdir vem de model_artifact.artifact_dir (DB-owned), mas o vocab.pkl é lido com
        # pickle.load IRRESTRITO (≠ torch.load weights_only=True do .pt). Um artifact_dir
        # adulterado/fora-da-árvore apontaria a desserialização para um .pkl arbitrário ⇒ RCE.
        # Mesma guarda resolve-depois-confere de _version_dir ANTES de abrir o .pkl.
        path = Path(ConfinedPath(vdir, root=self._base))
        meta = json.loads((path / "config.json").read_text())
        with open(path / "vocab.pkl", "rb") as f:
            vocab = pickle.load(f)
        # Todos os args de construção saem do meta — reconstrução determinística (Pitfall 1).
        # input_dim (2M) e output_dim (M) são distintos no CodeDKTModel real — usar os valores
        # gravados, não assumir input_dim==output_dim (Pitfall 1).
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
        # o state_dict é dict[str, Tensor], totalmente suportado nesse modo (WR-01).
        model.load_state_dict(
            torch.load(path / "model.pt", map_location="cpu", weights_only=True)
        )
        model.eval()
        return model, vocab, meta

    def persist(
        self,
        conn: sqlite3.Connection,
        turma_id: int,
        assignment_id: int,
        model: torch.nn.Module,
        vocab: dict,
        config: dict,
        first_auc: Optional[float] = None,
        git_commit: Optional[str] = None,
        data_hash: Optional[str] = None,
    ) -> dict:
        """Grava o blob write-once e insere a linha ModelArtifact — passos (1) e (2) da ordem.

        O blob é gravado FORA da transação (CR-01): se save_version ficasse dentro do BEGIN
        IMMEDIATE, uma falha do INSERT/COMMIT desfaria o banco mas deixaria o diretório v<N>
        órfão no FS — e a próxima persist() recalcularia o mesmo N e bateria em FileExistsError,
        travando o slot. A versão é calculada fora da txn sem corrida porque a trava global
        (PipelineLock, D-07) garante um único writer por vez; UNIQUE(assignment_id,
        version_number) segue como rede. A txn cobre só o INSERT; em qualquer falha, o
        ROLLBACK limpa o banco e o rmtree desfaz o blob recém-escrito, liberando o slot. NÃO
        faz o flip: o ponteiro current só é trocado por flip_current depois (passo (3),
        Pitfall 2). Devolve version_number, artifact_id, dir e content_hash."""
        version_number = next_version_number(conn, assignment_id)
        saved = self.save_version(
            turma_id, assignment_id, version_number, model, vocab, config
        )

        try:
            with transaction(conn):
                cur = conn.execute(
                    "INSERT INTO model_artifact "
                    "(assignment_id, version_number, content_hash, artifact_dir, created_at, "
                    "first_auc, git_commit, data_hash) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                    (
                        assignment_id,
                        version_number,
                        saved["content_hash"],
                        saved["dir"],
                        utc_now_iso(),
                        first_auc,  # DASH-05: o AUC do treino entra na linha junto do blob (D-05)
                        # Proveniência (0008): qual código e qual dado produziram esta versão.
                        git_commit,
                        data_hash,
                    ),
                )
                artifact_id = cur.lastrowid
        except BaseException:
            # O transaction() já deu ROLLBACK; aqui se desfaz o blob do passo 1 para o slot de
            # versão não ficar bloqueado (CR-01).
            vdir = Path(saved["dir"])
            if vdir.exists():
                shutil.rmtree(vdir)
            raise
        return {
            "version_number": version_number,
            "artifact_id": artifact_id,
            "dir": saved["dir"],
            "content_hash": saved["content_hash"],
        }
