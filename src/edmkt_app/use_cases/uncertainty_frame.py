"""Moldura de incerteza (DASH-05/D-08), compartilhada por mastery e recomendações.

TODA resposta derivada do modelo carrega first_auc + trained_at — nunca um veredito cru. Sem
modelo publicado a moldura vem NULA e a matriz vazia, e ainda assim é resposta enquadrada, não
um 404: "ainda não treinado" é um estado legítimo do produto.
"""

from __future__ import annotations

import sqlite3

from edmkt_app import mastery_service
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos


def uncertainty_frame(
    conn: sqlite3.Connection, assignment: models.Assignment
) -> tuple[dict[tuple[str, int], float], object, object]:
    if assignment.current_version_id is None:
        return {}, None, None
    artifact = repos.ModelArtifactRepository(conn).get(assignment.current_version_id)
    if artifact is None:
        return {}, None, None
    return mastery_service.compute_mastery(conn, assignment.id), artifact.first_auc, artifact.created_at
