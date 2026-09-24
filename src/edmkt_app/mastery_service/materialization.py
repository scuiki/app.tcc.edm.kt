"""Compute-once: a matriz aluno×KC é materializada UMA vez por artefato e servida do SQLite.

Gatilho lazy na primeira leitura do dashboard (D-65), o que mantém `train.py` intocado. A
agregação em si é do seam PURO `ml.mastery`; aqui só há orquestração e I/O (T-06-11).
"""

from __future__ import annotations
from api.knowledge_components.infrastructure.sqlite_qmatrix_repository import SqliteQMatrixRepository

import sqlite3

from ml.mastery.mastery_aggregation import aggregate_student_mastery

from edmkt_app.mastery_service import inference
from api.shared.infrastructure.database.sqlite_connection import transaction
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos


def _qmatrix_dict(conn: sqlite3.Connection, assignment_id: int) -> dict[int, list[int]]:
    # Q-matrix aprovada (problem_id → [kc_id...]) no shape que o seam puro aggregate_student_mastery
    # consome. Um problema pode ligar vários KCs (a média problem→KC é do core, Pitfall 2).
    qdict: dict[int, list[int]] = {}
    for binding in SqliteQMatrixRepository(conn).list_by_assignment(assignment_id):
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
    PURO ml.mastery.aggregate_student_mastery → persiste cada (subject_id, kc_id, mastery)
    via MasteryPredictionRepository.insert keyed ao artifact_id → devolve a matriz.
    """
    # Pelo módulo, não por `from ... import`: a referência importada congela no import e o
    # monkeypatch do teste (que prova a resolução-única, WR-02) deixaria de alcançar.
    _asg, artifact = inference._resolve_current_artifact(conn, assignment_id)
    pred_repo = repos.MasteryPredictionRepository(conn)

    if pred_repo.count_by_artifact(artifact.id) > 0:
        return _matrix_from_persisted(conn, artifact.id)

    # WR-02: passa o artefato já resolvido (linha 155) em vez de deixar infer_predictions
    # re-resolver — garante que as linhas keyed ao artifact.id e o modelo são a MESMA versão.
    pred_df = inference.infer_predictions(conn, assignment_id, artifact=artifact)
    qdict = _qmatrix_dict(conn, assignment_id)
    matrix = aggregate_student_mastery(pred_df, qdict)  # agregação no core puro (DIP)

    # CR-01: a conn está em autocommit (isolation_level=None, db.py); sem uma transação
    # explícita CADA insert commitaria sozinho e uma falha no meio do loop deixaria um cache
    # parcial que o guard compute-once serviria para sempre como se fosse a matriz completa.
    # transaction() (BEGIN IMMEDIATE/COMMIT, rollback em qualquer exceção) torna o write atômico.
    with transaction(conn):
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
    return matrix
