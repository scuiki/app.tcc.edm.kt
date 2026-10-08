# SqliteCandidateKnowledgeComponentRepository, os KCs candidatos pela ordem da resposta do LLM.

from __future__ import annotations

import sqlite3

import pytest

from api.knowledge_components.domain.entities.candidate_knowledge_component_entity import (
    CandidateKnowledgeComponent,
)
from api.knowledge_components.infrastructure.repositories.sqlite_candidate_knowledge_component_repository import (
    SqliteCandidateKnowledgeComponentRepository,
)
from tests.fixtures.assignments import add_assignment
from tests.fixtures.classrooms import add_classroom
from tests.fixtures.problems import add_problems


def _seed(conn) -> tuple[int, int]:
    # Um exercício com dois problemas e um conceito
    assignment_id = add_assignment(conn, add_classroom(conn))
    add_problems(conn, assignment_id, [1, 2])
    kc_id = conn.execute(
        "INSERT INTO kc (assignment_id, name) VALUES (?, 'laços');", (assignment_id,)
    ).lastrowid
    return assignment_id, kc_id


def test_the_candidates_come_back_by_problem_and_answer_order(tmp_db):
    repo = SqliteCandidateKnowledgeComponentRepository(tmp_db)
    assignment_id, kc_id = _seed(tmp_db)
    candidates = [
        CandidateKnowledgeComponent(assignment_id, 2, 1, "While loop", "uses while", kc_id),
        CandidateKnowledgeComponent(assignment_id, 1, 2, "For loop", "uses for", kc_id),
        CandidateKnowledgeComponent(assignment_id, 1, 1, "Loop", "loops", kc_id, "repete"),
    ]

    repo.add_many(candidates)

    assert repo.list_by_assignment(assignment_id) == [candidates[2], candidates[1], candidates[0]]


def test_a_candidate_must_fall_in_an_existing_concept(tmp_db):
    assignment_id, _ = _seed(tmp_db)
    with pytest.raises(sqlite3.IntegrityError):
        SqliteCandidateKnowledgeComponentRepository(tmp_db).add_many(
            [CandidateKnowledgeComponent(assignment_id, 1, 1, "Loop", "loops", 999_999)]
        )
