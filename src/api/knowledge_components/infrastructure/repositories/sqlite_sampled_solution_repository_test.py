# SqliteSampledSolutionRepository, as soluções amostradas pela execução e pela posição no prompt.

from __future__ import annotations

import sqlite3

import pytest

from api.knowledge_components.domain.entities.sampled_solution_entity import SampledSolution
from api.knowledge_components.infrastructure.repositories.sqlite_sampled_solution_repository import (
    SqliteSampledSolutionRepository,
)
from tests.fixtures.assignments import add_assignment
from tests.fixtures.classrooms import add_classroom
from tests.fixtures.problems import add_problems


def _seed(conn) -> tuple[int, list[int]]:
    # Um exercício com dois problemas e três execuções corretas no problema 1
    assignment_id = add_assignment(conn, add_classroom(conn))
    add_problems(conn, assignment_id, [1, 2])
    submission_ids = [
        conn.execute(
            "INSERT INTO submission (assignment_id, student_id, problem_id, code_snapshot_id, "
            "code, submitted_at, event_type, is_correct) "
            "VALUES (?, ?, 1, ?, 'int f(){return 1;}', 't0', 'Run.Program', 1);",
            (assignment_id, f"S{i}", f"c{i}"),
        ).lastrowid
        for i in range(3)
    ]
    return assignment_id, submission_ids


def test_the_sampled_solutions_come_back_in_prompt_order(tmp_db):
    repo = SqliteSampledSolutionRepository(tmp_db)
    assignment_id, submission_ids = _seed(tmp_db)
    solutions = [
        SampledSolution(assignment_id, 1, 2, submission_ids[0]),
        SampledSolution(assignment_id, 1, 1, submission_ids[2]),
    ]

    repo.add_many(solutions)

    assert repo.list_by_assignment(assignment_id) == [solutions[1], solutions[0]]


def test_a_sampled_solution_must_point_to_an_existing_run(tmp_db):
    assignment_id, _ = _seed(tmp_db)
    with pytest.raises(sqlite3.IntegrityError):
        SqliteSampledSolutionRepository(tmp_db).add_many(
            [SampledSolution(assignment_id, 1, 1, 999_999)]
        )
