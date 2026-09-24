# Duas turmas ativas não têm o mesmo nome, comparado sem diferença de caixa e de espaços.

from __future__ import annotations

from typing import Any

from api.classrooms.domain.interfaces.classroom_repository import IClassroomRepository
from api.classrooms.domain.value_objects.classroom_slug import ClassroomSlug


class ClassroomNameIsAvailableRule:
    def __init__(self, classrooms: IClassroomRepository) -> None:
        self._classrooms = classrooms

    def check(self, dto: Any) -> str | None:
        wanted = ClassroomSlug.from_name(dto.name)
        # Renomear para o próprio nome, com outra grafia, não é conflito
        own_id = getattr(dto, "classroom_id", None)
        for classroom in self._classrooms.list_all():
            if classroom.id != own_id and ClassroomSlug.from_name(classroom.name) == wanted:
                return f"já existe uma turma chamada {classroom.name!r}"
        return None
