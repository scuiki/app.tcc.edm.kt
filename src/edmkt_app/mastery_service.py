"""Orquestração impura do mastery (D-04): load → infer → aggregate → persist.

Camada DIP que liga o modelo Code-DKT treinado + a Q-matrix aprovada ao seam PURO
`edmkt_core.mastery`. Espelha a forma de `train.py:_train_body` (resolve nomes→ids → lê o
Parquet canônico da Fase 3 → recarrega o artefato via `ArtifactStore.load_version` →
reconstrói as entradas de inferência do MESMO jeito que `pipeline.py` → chama
`predict_code_dkt` → mapeia ProblemID→KC pela Q-matrix → constrói a matriz aluno×KC pelo
seam puro → persiste em `mastery_prediction`). TODO I/O de FS/SQLite/torch vive aqui; toda
agregação fica no core puro (`edmkt_core.mastery`).

Compute-once (T-06-11, DoS): a matriz é materializada UMA vez por artefato e servida do
SQLite — `compute_mastery` checa `MasteryPredictionRepository.count_by_artifact` e, se já
existe, reconstrói a matriz das linhas persistidas em vez de re-inferir. Gatilho = lazy na
primeira leitura do dashboard (D-65), o que mantém `train.py` intocado.

Segurança: o vocab da inferência é SEMPRE o recarregado do artefato (nunca reconstruído —
sem vazamento de partição); o reload passa SÓ por `load_version` (que desserializa com
weights_only=True em artifacts.py) — este módulo nunca chama a desserialização solta do
torch; o caminho do Parquet sai de int IDs + `_slug` interno, nunca de caminho de cliente
(T-06-09/T-06-10).
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

from edmkt_core.evaluation import build_problem_index
from edmkt_core.features import build_cache
from edmkt_core.mastery import build_mastery_matrix
from edmkt_core.models.code_dkt import predict_code_dkt
from edmkt_core.sequences import build_sequences

from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.artifacts import ArtifactStore

# Raiz do FS de dados; override por teste/deploy (mesma convenção de train.DATA_ROOT).
DATA_ROOT = Path("data")


def _slug(name: str) -> str:
    # Mesma forma de train._slug / features_cache._slug: o diretório da turma vem do slug
    # interno, nunca de nome de upload.
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "turma"


def _progsnap_aid(assignment_name: str) -> int:
    # O AssignmentID do ProgSnap2 (nome do Parquet) é o sufixo numérico do nome do assignment,
    # igual a train._progsnap_aid; build_sequences também o consome.
    m = re.search(r"(\d+)", assignment_name)
    if m is None:
        raise ValueError(f"AssignmentID não derivável do nome: {assignment_name!r}")
    return int(m.group(1))


def _resolve_current_artifact(
    conn: sqlite3.Connection, assignment_id: int
) -> tuple[models.Assignment, models.ModelArtifact]:
    """Resolve o assignment + o ModelArtifact apontado por current_version_id (D-06).

    Levanta ValueError se o assignment não existe ou ainda não tem um artefato publicado —
    o caminho de leitura do dashboard só faz sentido sobre um modelo treinado e flipado.
    """
    asg = repos.AssignmentRepository(conn).get(assignment_id)
    if asg is None:
        raise ValueError(f"assignment {assignment_id} inexistente")
    if asg.current_version_id is None:
        raise ValueError(f"assignment {assignment_id} sem modelo publicado (current_version_id None)")
    artifact = repos.ModelArtifactRepository(conn).get(asg.current_version_id)
    if artifact is None:
        raise ValueError(f"model_artifact {asg.current_version_id} inexistente")
    return asg, artifact


def infer_predictions(conn: sqlite3.Connection, assignment_id: int) -> pd.DataFrame:
    """Carrega o artefato current + roda predict_code_dkt sobre as sequências da turma.

    Recarrega o modelo E o vocab via `load_version` (weights_only=True) — o vocab NUNCA é
    reconstruído (mesma garantia de pipeline.py: o reload é a fonte). As entradas de
    inferência são montadas na mesma ordem de pipeline.train_and_evaluate: build_sequences →
    build_cache (paths crus) → build_problem_index. Devolve o pred_df cru (user_id, skill_name,
    correct, is_first_attempt, correct_predictions) — sem tocar o banco.
    """
    asg, artifact = _resolve_current_artifact(conn, assignment_id)
    turma = repos.TurmaRepository(conn).get(asg.turma_id)
    turma_slug = _slug(turma.name)
    progsnap_aid = _progsnap_aid(asg.name)

    pq = DATA_ROOT / turma_slug / "clean" / f"assignment_{progsnap_aid}.parquet"
    df = pd.read_parquet(pq, engine="pyarrow")

    # artifact_dir é DB-owned (reconstruído do valor gravado, nunca de caminho de cliente);
    # load_version desserializa com weights_only=True (artifacts.py) — sem reload solto (T-06-09).
    model, vocab, meta = ArtifactStore(str(DATA_ROOT)).load_version(artifact.artifact_dir)

    max_len = meta.get("max_len", 50)
    R = meta.get("R", 50)

    # Mesma montagem de pipeline.py: sequências completas → cache de paths crus → índice de
    # problemas global. O vocab vem do artefato (meta/vocab), nunca reconstruído (CORE-04).
    sequences = build_sequences(df, progsnap_aid)
    code_states = dict(zip(df["CodeStateID"].astype(str), df["Code"].fillna("")))
    all_csids: set[str] = set()
    for seq in sequences:
        all_csids.update(seq["events"]["CodeStateID"].astype(str).tolist())
    cache_raw = build_cache(
        sorted(all_csids),
        code_states,
        max_path_length=meta.get("max_path_length", 8),
        max_path_width=meta.get("max_path_width", 2),
        R=R,
        seed=meta.get("seed", 42),
        n_workers=None,
    )
    problem_to_idx = build_problem_index(sequences)

    return predict_code_dkt(
        model, sequences, problem_to_idx, vocab, cache_raw, max_len=max_len, R=R
    )


def _qmatrix_dict(conn: sqlite3.Connection, assignment_id: int) -> dict[int, list[int]]:
    # Q-matrix aprovada (problem_id → [kc_id...]) no shape que o seam puro build_mastery_matrix
    # consome. Um problema pode ligar vários KCs (a média problem→KC é do core, Pitfall 2).
    qdict: dict[int, list[int]] = {}
    for binding in repos.QMatrixRepository(conn).list_by_assignment(assignment_id):
        qdict.setdefault(binding.problem_id, []).append(binding.kc_id)
    return qdict


def _matrix_from_persisted(
    conn: sqlite3.Connection, artifact_id: int
) -> dict[tuple[str, int], float]:
    # Reconstrói a matriz {(subject_id, kc_id): mastery} das linhas já materializadas — o
    # caminho compute-once: servir do SQLite sem re-inferir (T-06-11).
    rows = repos.MasteryPredictionRepository(conn).list_by_artifact(artifact_id)
    return {(r.subject_id, r.kc_id): r.mastery for r in rows}


def compute_mastery(
    conn: sqlite3.Connection, assignment_id: int
) -> dict[tuple[str, int], float]:
    """Matriz aluno×KC do assignment, materializada uma vez e servida do SQLite (D-04, D-65).

    Compute-once: se mastery_prediction já tem linhas para o artefato current, serve delas
    (sem re-inferir). Caso contrário, infere (infer_predictions) → constrói a matriz pelo seam
    PURO edmkt_core.mastery.build_mastery_matrix → persiste cada (subject_id, kc_id, mastery)
    via MasteryPredictionRepository.insert keyed ao artifact_id → devolve a matriz.
    """
    _asg, artifact = _resolve_current_artifact(conn, assignment_id)
    pred_repo = repos.MasteryPredictionRepository(conn)

    if pred_repo.count_by_artifact(artifact.id) > 0:
        return _matrix_from_persisted(conn, artifact.id)

    pred_df = infer_predictions(conn, assignment_id)
    qdict = _qmatrix_dict(conn, assignment_id)
    matrix = build_mastery_matrix(pred_df, qdict)  # agregação no core puro (DIP)

    for (subject_id, kc_id), mastery in matrix.items():
        pred_repo.insert(
            models.MasteryPrediction(
                id=None,
                model_artifact_id=artifact.id,
                subject_id=subject_id,
                kc_id=kc_id,
                mastery=float(mastery),
            )
        )
    conn.commit()
    return matrix
