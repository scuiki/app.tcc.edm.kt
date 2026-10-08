# SqliteProblemRepository, ida e volta, ordem por problema e o enunciado.

from __future__ import annotations

import sqlite3

import pytest

from api.assignments.problems.domain.entities.problem_entity import Problem
from api.assignments.problems.infrastructure.repositories.sqlite_problem_repository import (
    SqliteProblemRepository,
)
from tests.fixtures.assignments import add_assignment
from tests.fixtures.classrooms import add_classroom


def test_the_problems_come_back_ordered_and_without_description(tmp_db):
    repo = SqliteProblemRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))

    repo.add_many([Problem(assignment_id, 13), Problem(assignment_id, 1)])

    assert repo.list_by_assignment(assignment_id) == [
        Problem(assignment_id, 1),
        Problem(assignment_id, 13),
    ]


def test_the_same_problem_id_is_a_different_problem_in_another_assignment(tmp_db):
    repo = SqliteProblemRepository(tmp_db)
    classroom_id = add_classroom(tmp_db)
    first, second = add_assignment(tmp_db, classroom_id), add_assignment(tmp_db, classroom_id)

    repo.add_many([Problem(first, 1), Problem(second, 1)])

    assert repo.list_by_assignment(second) == [Problem(second, 1)]


def test_a_problem_is_unique_within_its_assignment(tmp_db):
    repo = SqliteProblemRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    repo.add_many([Problem(assignment_id, 1)])

    with pytest.raises(sqlite3.IntegrityError):
        repo.add_many([Problem(assignment_id, 1)])


def test_the_statement_goes_and_comes_back(tmp_db):
    repo = SqliteProblemRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))

    repo.add_many(
        [Problem(assignment_id, 1, statement="Soma dois números"), Problem(assignment_id, 2)]
    )

    statements = [p.statement for p in repo.list_by_assignment(assignment_id)]
    assert statements == ["Soma dois números", None]
