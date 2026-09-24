# SqliteProblemRepository, ida e volta, ordem por problema e a descrição gravada depois.

from __future__ import annotations

import sqlite3

import pytest

from api.assignments.problems.domain.entities.problem_entity import Problem
from api.assignments.problems.infrastructure.repositories.sqlite_problem_repository import (
    SqliteProblemRepository,
)


def _assignment_id(conn) -> int:
    classroom_id = conn.execute(
        "INSERT INTO classroom (name, created_at) VALUES ('T', 't0');"
    ).lastrowid
    return conn.execute(
        "INSERT INTO assignment (classroom_id, name, created_at) VALUES (?, 'A', 't0');",
        (classroom_id,),
    ).lastrowid


def test_the_problems_come_back_ordered_and_without_description(tmp_db):
    repo = SqliteProblemRepository(tmp_db)
    assignment_id = _assignment_id(tmp_db)

    repo.add_many([Problem(assignment_id, 13), Problem(assignment_id, 1)])

    assert repo.list_by_assignment(assignment_id) == [
        Problem(assignment_id, 1),
        Problem(assignment_id, 13),
    ]


def test_descriptions_are_written_only_for_the_given_problems(tmp_db):
    repo = SqliteProblemRepository(tmp_db)
    assignment_id = _assignment_id(tmp_db)
    repo.add_many([Problem(assignment_id, 1), Problem(assignment_id, 2)])

    repo.set_descriptions(assignment_id, {2: "Soma os elementos de um array"})

    assert [p.description for p in repo.list_by_assignment(assignment_id)] == [
        None,
        "Soma os elementos de um array",
    ]


def test_the_same_problem_id_is_a_different_problem_in_another_assignment(tmp_db):
    repo = SqliteProblemRepository(tmp_db)
    first, second = _assignment_id(tmp_db), _assignment_id(tmp_db)

    repo.add_many([Problem(first, 1), Problem(second, 1)])

    assert repo.list_by_assignment(second) == [Problem(second, 1)]


def test_a_problem_is_unique_within_its_assignment(tmp_db):
    repo = SqliteProblemRepository(tmp_db)
    assignment_id = _assignment_id(tmp_db)
    repo.add_many([Problem(assignment_id, 1)])

    with pytest.raises(sqlite3.IntegrityError):
        repo.add_many([Problem(assignment_id, 1)])
