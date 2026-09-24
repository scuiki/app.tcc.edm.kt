"""Regra: recusa importar de novo uma turma que já existe.

Sem ela, subir a mesma turma de novo criava turma, assignments e submissões duplicados, e as duas
turmas dividiam o MESMO diretório em data/ (o caminho vem do slug): o cache de paths, as respostas
do LLM e os modelos de uma se misturavam com os da outra. Nada disso dava erro.

A comparação é pelo SLUG, não pelo nome: "Turma 6" e "turma  6" são nomes diferentes e o MESMO
diretório. É uma parede explícita até existir re-treino com dados novos: falhar alto é melhor que
corromper em silêncio.
"""

from __future__ import annotations

from typing import Any

from api.assignments.domain.interfaces.classroom_repository import IClassroomRepository
from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug


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
