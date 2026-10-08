# SqliteKnowledgeComponentEvidenceRepository, os trechos de cada conceito por problema.

from __future__ import annotations

import sqlite3

import pytest

from api.knowledge_components.domain.entities.knowledge_component_evidence_entity import (
    KnowledgeComponentEvidence,
)
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_evidence_repository import (
    SqliteKnowledgeComponentEvidenceRepository,
)
from tests.fixtures.assignments import add_assignment
from tests.fixtures.classrooms import add_classroom
from tests.fixtures.problems import add_problems


def _seed(conn) -> tuple[int, int, int]:
    # Um exercício com dois problemas, uma solução amostrada em cada e dois conceitos
    assignment_id = add_assignment(conn, add_classroom(conn))
    add_problems(conn, assignment_id, [1, 2])
    for problem_id in (1, 2):
        submission_id = conn.execute(
            "INSERT INTO submission (assignment_id, student_id, problem_id, code_snapshot_id, "
            "code, submitted_at, event_type, is_correct) "
            "VALUES (?, 'S1', ?, 'c', 'int f(){return 1;}', 't0', 'Run.Program', 1);",
            (assignment_id, problem_id),
        ).lastrowid
        conn.execute(
            "INSERT INTO sampled_solution (assignment_id, problem_id, position, submission_id) "
            "VALUES (?, ?, 1, ?);",
            (assignment_id, problem_id, submission_id),
        )
    loops, conditionals = (
        conn.execute("INSERT INTO kc (assignment_id, name) VALUES (?, ?);", (assignment_id, name)).lastrowid
        for name in ("Laços", "Condicionais")
    )
    return assignment_id, loops, conditionals


def test_the_evidence_comes_back_by_problem_and_concept(tmp_db):
    repo = SqliteKnowledgeComponentEvidenceRepository(tmp_db)
    assignment_id, loops, conditionals = _seed(tmp_db)
    evidence = [
        KnowledgeComponentEvidence(assignment_id, 2, loops, 1, 3, 4),
        KnowledgeComponentEvidence(assignment_id, 1, conditionals, 1, 2, 2),
        KnowledgeComponentEvidence(assignment_id, 1, loops, 1, 1, 1),
    ]

    repo.add_many(evidence)

    assert repo.list_by_assignment(assignment_id) == sorted(
        evidence, key=lambda e: (e.problem_id, e.kc_id)
    )


def test_a_snippet_must_be_in_a_sampled_solution(tmp_db):
    assignment_id, loops, _ = _seed(tmp_db)
    with pytest.raises(sqlite3.IntegrityError):
        SqliteKnowledgeComponentEvidenceRepository(tmp_db).add_many(
            [KnowledgeComponentEvidence(assignment_id, 1, loops, 2, 1, 1)]
        )
