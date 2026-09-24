"""ClassroomNotImportedYetRule: a mesma turma não é importada duas vezes, comparando pelo slug."""

from __future__ import annotations

from types import SimpleNamespace

from api.assignments.domain.classroom_entity import Classroom
from api.classroom_import.domain.classroom_not_imported_yet_rule import ClassroomNotImportedYetRule


class _InMemoryClassrooms:
    def __init__(self, *names: str) -> None:
        self._classrooms = [Classroom(id=i, name=n, created_at="t0") for i, n in enumerate(names)]

    def list_all(self) -> list[Classroom]:
        return self._classrooms


def test_refuses_a_name_whose_slug_already_exists():
    # Nome diferente, MESMO slug ("turma-x"): é o diretório que colide, não a string.
    rule = ClassroomNotImportedYetRule(_InMemoryClassrooms("Turma X"))

    message = rule.check(SimpleNamespace(classroom_name="  turma   x  "))

    assert message is not None and "já foi importada" in message


def test_allows_a_new_classroom():
    rule = ClassroomNotImportedYetRule(_InMemoryClassrooms("Turma X"))

    assert rule.check(SimpleNamespace(classroom_name="Turma Y")) is None
