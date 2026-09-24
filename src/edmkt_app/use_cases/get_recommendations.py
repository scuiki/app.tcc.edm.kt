"""Ranking de reforço pelos KCs de menor mastery, texto pt-BR e ZERO LLM (REC-01/D-07)."""

from __future__ import annotations
from api.knowledge_components.infrastructure.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)

import sqlite3

from edmkt_app.mastery_rules import find_critical_knowledge_components

from edmkt_app.recommendations import recommend_reinforcement
from edmkt_app.use_cases.base import require_assignment
from edmkt_app.use_cases.uncertainty_frame import uncertainty_frame


class GetRecommendationsUseCase:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, assignment_id: int) -> dict:
        assignment = require_assignment(self._conn, assignment_id)
        matrix, _first_auc, _trained_at = uncertainty_frame(self._conn, assignment)
        names = {
            kc.id: kc.name
            for kc in SqliteKnowledgeComponentRepository(self._conn).list_by_assignment(assignment_id)
        }
        kc_means = [
            (kc_id, names.get(kc_id, f"KC {kc_id}"), mean)
            for kc_id, mean in find_critical_knowledge_components(matrix)
        ]
        return {
            "assignment_id": assignment_id,
            "recommendations": recommend_reinforcement(kc_means),
        }
