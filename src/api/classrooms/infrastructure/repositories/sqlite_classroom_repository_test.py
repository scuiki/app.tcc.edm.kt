# SqliteClassroomRepository, ida e volta fiel, e SQL parametrizado.

from __future__ import annotations

from api.classrooms.domain.entities.classroom_entity import Classroom
from api.classrooms.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)


def test_add_then_get_returns_the_same_classroom(tmp_db):
    repository = SqliteClassroomRepository(tmp_db)

    classroom_id = repository.add(Classroom(id=None, name="Turma A", created_at="t0"))

    assert repository.get(classroom_id) == Classroom(id=classroom_id, name="Turma A", created_at="t0")
    assert repository.get(999) is None


def test_list_all_is_ordered_by_id(tmp_db):
    repository = SqliteClassroomRepository(tmp_db)
    first = repository.add(Classroom(id=None, name="B", created_at="t0"))
    second = repository.add(Classroom(id=None, name="A", created_at="t0"))

    assert [c.id for c in repository.list_all()] == [first, second]


def test_a_malicious_name_is_stored_as_data_not_executed(tmp_db):
    repository = SqliteClassroomRepository(tmp_db)
    evil = "x'); DROP TABLE classroom; --"

    classroom_id = repository.add(Classroom(id=None, name=evil, created_at="t0"))

    assert repository.get(classroom_id).name == evil
    tmp_db.execute("SELECT 1 FROM classroom LIMIT 1;")  # a tabela continua lá
