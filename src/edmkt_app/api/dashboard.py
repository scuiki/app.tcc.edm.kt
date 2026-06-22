"""Router /dashboard — API JSON read-only do slice de backend (DASH-01..05, REC-01, 999.2).

Espelha api/training.py / api/kc.py: APIRouter + `conn = Depends(get_conn)` por requisição,
ids inteiros tipados (path param), nunca strings (V5). Toda rota é GET sem efeito colateral
de escrita visível ao cliente — o único write é a materialização lazy compute-once da matriz
de mastery, que vive em mastery_service (T-06-15). O frontend (React SPA, D-02/D-03) é o
consumidor adiado desta MESMA API; não há frontend neste slice.

Moldura de incerteza (DASH-05/D-08): TODA resposta de mastery carrega first_auc + trained_at
(model_artifact.created_at) — nunca um veredito cru. Antes do treino o assignment não tem
modelo publicado: a resposta vem com a moldura nula (first_auc=None, trained_at=None) e matriz
vazia, e ainda assim é uma resposta enquadrada, não um 404.

Segurança: ids são int (path); os caminhos de FS saem de int IDs + _slug/_progsnap_aid internos
(mastery_service / eda), nunca de caminho de cliente (T-06-12); todo SQL é parametrizado pelos
repositórios (T-06-13).
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from edmkt_core.mastery import at_risk_students, critical_kcs
from edmkt_app import eda as eda_module
from edmkt_app import mastery_service
from edmkt_app.api.deps import get_conn
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.recommendations import recommend_reinforcement

router = APIRouter(tags=["dashboard"])


def _require_assignment(conn: sqlite3.Connection, assignment_id: int) -> models.Assignment:
    # V5: id inteiro inexistente → 404 explícito (nunca segue para SQL/FS com id inválido).
    assignment = repos.AssignmentRepository(conn).get(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="assignment inexistente")
    return assignment


def _kc_names(conn: sqlite3.Connection, assignment_id: int) -> dict[int, str]:
    return {
        kc.id: kc.name
        for kc in repos.KCRepository(conn).list_by_assignment(assignment_id)
    }


def _uncertainty_frame(
    conn: sqlite3.Connection, assignment: models.Assignment
) -> tuple[dict[tuple[str, int], float], object, object]:
    """Matriz aluno×KC + (first_auc, trained_at) do artefato current.

    Sem modelo publicado (current_version_id None) a moldura é nula e a matriz vazia — a
    resposta ainda vai enquadrada (D-08), só sinaliza "ainda não treinado". Com modelo,
    delega o compute-once a mastery_service e lê first_auc/created_at do model_artifact.
    """
    if assignment.current_version_id is None:
        return {}, None, None

    artifact = repos.ModelArtifactRepository(conn).get(assignment.current_version_id)
    if artifact is None:
        return {}, None, None

    matrix = mastery_service.compute_mastery(conn, assignment.id)
    return matrix, artifact.first_auc, artifact.created_at


@router.get("/dashboard/mastery/{assignment_id}")
def get_mastery(
    assignment_id: int, conn: sqlite3.Connection = Depends(get_conn)
) -> dict:
    assignment = _require_assignment(conn, assignment_id)
    matrix, first_auc, trained_at = _uncertainty_frame(conn, assignment)

    # matrix interna usa chave-tupla (subject_id, kc_id); achata para o payload JSON.
    cells = [
        {"subject_id": subject_id, "kc_id": kc_id, "mastery": mastery}
        for (subject_id, kc_id), mastery in matrix.items()
    ]
    critical = [{"kc_id": kc_id, "mean_mastery": mean} for kc_id, mean in critical_kcs(matrix)]
    return {
        "assignment_id": assignment_id,
        "first_auc": first_auc,  # DASH-05/D-08: moldura de incerteza sempre presente
        "trained_at": trained_at,
        "matrix": cells,  # DASH-01: aluno×KC
        "critical_kcs": critical,  # DASH-02: KCs mais fracos primeiro
        "at_risk_students": at_risk_students(matrix),  # DASH-03
    }


@router.get("/dashboard/eda/{assignment_id}")
def get_eda(
    assignment_id: int, conn: sqlite3.Connection = Depends(get_conn)
) -> dict:
    # DASH-04: a EDA roda SEM modelo treinado — só lê o Parquet canônico. Se o Parquet ainda
    # não existe (turma sem ingestão concluída), degrada para agregados vazios em vez de 500.
    assignment = _require_assignment(conn, assignment_id)
    turma = repos.TurmaRepository(conn).get(assignment.turma_id)
    pq = eda_module.canonical_parquet_path(turma.name, assignment.name)

    if not pq.exists():
        return {
            "assignment_id": assignment_id,
            "success_rate": {},
            "learning_curve": {},
            "compile_error_rate": {},
        }
    return {
        "assignment_id": assignment_id,
        "success_rate": eda_module.success_rate_by_assignment(pq),
        "learning_curve": eda_module.learning_curve(pq),
        "compile_error_rate": eda_module.compile_error_rate_by_assignment(pq),
    }


@router.get("/dashboard/recommendations/{assignment_id}")
def get_recommendations(
    assignment_id: int, conn: sqlite3.Connection = Depends(get_conn)
) -> dict:
    # REC-01: ranking puro dos KCs mais fracos (menor mastery primeiro) com texto pt-BR.
    assignment = _require_assignment(conn, assignment_id)
    matrix, _first_auc, _trained_at = _uncertainty_frame(conn, assignment)
    names = _kc_names(conn, assignment_id)
    kc_means = [
        (kc_id, names.get(kc_id, f"KC {kc_id}"), mean) for kc_id, mean in critical_kcs(matrix)
    ]
    return {
        "assignment_id": assignment_id,
        "recommendations": recommend_reinforcement(kc_means),
    }


@router.get("/assignments")
def list_assignments(conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    # BACKLOG 999.2: fecha a ambiguidade de id-space (Pitfall 5) que forçava query manual no
    # app.db na UAT da Fase 4 — expõe id do DB + id ProgSnap2 (derivado do name) + name + status.
    items = []
    for asg in repos.AssignmentRepository(conn).list_all():
        try:
            progsnap_id = mastery_service._progsnap_aid(asg.name)
        except ValueError:
            progsnap_id = None  # nome sem sufixo numérico: id ProgSnap2 indisponível, não quebra a lista
        items.append(
            {
                "id": asg.id,  # id interno do DB (autoincrement)
                "progsnap_id": progsnap_id,  # id ProgSnap2 (train.py:_progsnap_aid)
                "name": asg.name,
                "status": asg.status,
                "current_version_id": asg.current_version_id,
            }
        )
    return {"assignments": items}
