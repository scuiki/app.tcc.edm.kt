"""Carrega o artefato publicado e roda predict_code_dkt sobre as sequências da turma.

O vocab é SEMPRE o recarregado do artefato, nunca reconstruído — mesma garantia de pipeline.py:
o reload é a fonte, e reconstruir vazaria a partição. O reload passa só por `load_version`
(weights_only=True); este módulo nunca chama a desserialização solta do torch (T-06-09).
"""

from __future__ import annotations

import sqlite3

import pandas as pd

from edmkt_core.config import FROZEN_CONFIG
from edmkt_core.evaluation import build_problem_index
from edmkt_core.pipeline import code_state_ids, code_states_from_df
from edmkt_core.models.code_dkt import predict_code_dkt
from edmkt_core.sequences import build_sequences

from edmkt_app import data_layout
from edmkt_app.features_cache import build_cache_on_disk
from edmkt_app.modeling_frame import load_modeling_frame
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.artifacts import ArtifactStore


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


def infer_predictions(
    conn: sqlite3.Connection,
    assignment_id: int,
    artifact: models.ModelArtifact | None = None,
) -> pd.DataFrame:
    """Carrega o artefato current + roda predict_code_dkt sobre as sequências da turma.

    Recarrega o modelo E o vocab via `load_version` (weights_only=True) — o vocab NUNCA é
    reconstruído (mesma garantia de pipeline.py: o reload é a fonte). As entradas de
    inferência são montadas na mesma ordem de pipeline.train_and_evaluate: build_sequences →
    build_cache (paths crus) → build_problem_index. Devolve o pred_df cru (user_id, skill_name,
    correct, is_first_attempt, correct_predictions) — sem tocar o banco.

    WR-02: aceita um `artifact` já resolvido. compute_mastery resolve UMA vez e o thread aqui,
    de modo que as linhas persistidas (keyed ao artifact.id) e o modelo carregado são sempre a
    MESMA versão mesmo que um flip_current concorrente troque current_version_id entre as leituras
    (a conn está em autocommit). Sem ele, este método re-resolveria e poderia pegar outra versão.
    """
    if artifact is None:
        _asg, artifact = _resolve_current_artifact(conn, assignment_id)

    # Mesmíssima porta do treino: inferir sobre o stream misto alimentaria o modelo com eventos
    # que ele nunca viu, e a matriz do dashboard sairia de outra distribuição que o AUC exibido
    # na moldura de incerteza. A resolução nome→caminho e as guardas de assignment/turma
    # inexistentes vivem lá (modeling_frame), não duplicadas aqui.
    frame = load_modeling_frame(conn, assignment_id)
    df, progsnap_aid = frame.events, frame.assignment_id

    # artifact_dir é DB-owned (reconstruído do valor gravado, nunca de caminho de cliente);
    # load_version desserializa com weights_only=True (artifacts.py) — sem reload solto (T-06-09).
    store = ArtifactStore(str(data_layout.trained_models_dir(frame.turma_slug)))
    model, vocab, meta = store.load_version(artifact.artifact_dir)

    max_len = meta.get("max_len", 50)
    R = meta.get("R", 50)

    # Mesma montagem de pipeline.py: sequências completas → cache de paths crus → índice de
    # problemas global. O vocab vem do artefato (meta/vocab), nunca reconstruído (CORE-04).
    # .value: build_sequences é do core congelado e filtra df["progsnap_assignment_id"] pelo int.
    sequences = build_sequences(df, progsnap_aid.value)
    # O mesmo cache de paths em disco que o treino aqueceu: os snapshots já extraídos não são
    # extraídos de novo. Os parâmetros de extração são os do meta do artefato, completados pelos
    # hiperparâmetros congelados (que são os defaults com que todo artefato foi treinado).
    cache_raw = build_cache_on_disk(
        frame.turma_slug,
        sorted(set(code_state_ids(sequences))),
        code_states_from_df(df),
        {**FROZEN_CONFIG, **meta},
    )
    problem_to_idx = build_problem_index(sequences)

    return predict_code_dkt(
        model, sequences, problem_to_idx, vocab, cache_raw, max_len=max_len, R=R
    )
