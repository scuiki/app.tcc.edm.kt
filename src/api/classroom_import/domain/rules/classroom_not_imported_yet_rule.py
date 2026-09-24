# Sem esta regra, reimportar a mesma turma duplica dados e mistura o diretório de duas turmas.

from __future__ import annotations

from typing import Any

from api.classrooms.domain.interfaces.classroom_repository import IClassroomRepository
from api.classrooms.domain.value_objects.classroom_slug import ClassroomSlug


class ClassroomNotImportedYetRule:
    def __init__(self, classrooms: IClassroomRepository) -> None:
        self._classrooms = classrooms

    def check(self, dto: Any) -> str | None:
        target = ClassroomSlug.from_name(dto.classroom_name)
        for classroom in self._classrooms.list_all():
            if ClassroomSlug.from_name(classroom.name) == target:
                return (
                    f"a turma {classroom.name!r} já foi importada; reimportar ainda não é "
                    "suportado (use outro nome de turma ou remova a anterior)"
                )
        return None
