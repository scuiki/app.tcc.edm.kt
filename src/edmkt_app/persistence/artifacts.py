"""ArtifactStore write-once + versão monótona + content_hash + flip atômico (MODEL-04).

Coração do MODEL-04 (D-04/D-05/D-06). Cada versão de modelo é um diretório `v<N>`
write-once sob `base/<turma>/<assignment>/models/`, guardando os pesos (`state_dict`,
NUNCA o nn.Module — Anti-Pattern RESEARCH/CLAUDE.md §What NOT to Use), o `vocab.pkl` e um
`config.json` que carrega TODOS os args de construção do CodeDKTModel (Pitfall 1: sem eles o
`.pt` é irrecuperável por size mismatch no reload). O `version_number` é monótono por
(turma, assignment) e calculado na MESMA transação do insert (Pitfall 5); o `content_hash`
(SHA-256 dos três arquivos) é metadado de integridade/dedup, não identidade (D-04). O flip
do ponteiro `current_version_id` é o ÚLTIMO passo, um UPDATE atômico — a ordem load-bearing
blob→INSERT→flip garante que um leitor nunca siga o ponteiro para um artefato truncado
(Pitfall 2). Este módulo é o primeiro I/O de filesystem write-once do projeto.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import torch

from edmkt_core.models.code_dkt import CodeDKTModel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def next_version_number(conn: sqlite3.Connection, assignment_id: int) -> int:
    """Próxima versão = MAX(version_number)+1 dentro do escopo (assignment). Pattern 2.

    Deve rodar na MESMA transação do INSERT do artefato (Pitfall 5), senão dois inserts
    concorrentes calculam o mesmo número; UNIQUE(assignment_id, version_number) é a rede."""
    row = conn.execute(
        "SELECT COALESCE(MAX(version_number), 0) + 1 AS next FROM model_artifact "
        "WHERE assignment_id = ?;",
        (assignment_id,),
    ).fetchone()
    return int(row["next"])


def flip_current(conn: sqlite3.Connection, assignment_id: int, new_version_id: int) -> None:
    """Troca Assignment.current_version_id por um UPDATE atômico (Pattern 5 / D-06).

    O flip é o ÚLTIMO passo da ordem load-bearing (blob write-once → INSERT → flip): só
    aqui um leitor passa a enxergar a nova versão, e sempre uma já completa (Pitfall 2). O
    ponteiro no DB é a fonte única — este UPDATE nunca toca o diretório do artefato."""
    conn.execute("BEGIN IMMEDIATE;")
    try:
        conn.execute(
            "UPDATE assignment SET current_version_id=? WHERE id=?;",
            (new_version_id, assignment_id),
        )
        conn.execute("COMMIT;")
    except BaseException:
        conn.execute("ROLLBACK;")
        raise


class ArtifactStore:
    """Grava/relê versões de modelo write-once sob `base_path` (D-05/D-06).

    save_version escreve um diretório v<N> e devolve dir + content_hash; load_version
    reconstrói o CodeDKTModel pelo contrato de reload; persist amarra a versão monótona ao
    INSERT na mesma transação. O flip do ponteiro é função separada (flip_current), chamada
    DEPOIS que o blob e a linha já existem (ordem load-bearing, Pitfall 2)."""

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path)

    def _version_dir(self, turma_id: int, assignment_id: int, version_number: int) -> Path:
        # Componentes derivados de IDs inteiros internos (nunca de nomes de upload). Resolve
        # e valida que o diretório fica sob base — defesa contra traversal (RESEARCH §Security).
        base = self._base.resolve()
        vdir = (
            base / str(int(turma_id)) / str(int(assignment_id)) / "models"
            / f"v{int(version_number)}"
        )
        resolved = (base / vdir.relative_to(base)).resolve()
        if base not in resolved.parents and resolved != base:
            raise ValueError(f"path traversal: {resolved} fora de {base}")
        return vdir

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
        vdir = self._version_dir(turma_id, assignment_id, version_number)
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
        path = Path(vdir)
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
        model.load_state_dict(torch.load(path / "model.pt", map_location="cpu"))
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
    ) -> dict:
        """Grava o blob write-once e insere a linha ModelArtifact — passos (1) e (2) da ordem.

        A versão monótona e o INSERT acontecem na MESMA transação (Pitfall 5). NÃO faz o flip:
        o ponteiro current só é trocado por flip_current depois (passo (3), Pitfall 2). Devolve
        version_number, artifact_id, dir e content_hash."""
        conn.execute("BEGIN IMMEDIATE;")
        try:
            version_number = next_version_number(conn, assignment_id)
            saved = self.save_version(
                turma_id, assignment_id, version_number, model, vocab, config
            )
            cur = conn.execute(
                "INSERT INTO model_artifact "
                "(assignment_id, version_number, content_hash, artifact_dir, created_at) "
                "VALUES (?, ?, ?, ?, ?);",
                (
                    assignment_id,
                    version_number,
                    saved["content_hash"],
                    saved["dir"],
                    _now_iso(),
                ),
            )
            artifact_id = cur.lastrowid
            conn.execute("COMMIT;")
        except BaseException:
            conn.execute("ROLLBACK;")
            raise
        return {
            "version_number": version_number,
            "artifact_id": artifact_id,
            "dir": saved["dir"],
            "content_hash": saved["content_hash"],
        }
