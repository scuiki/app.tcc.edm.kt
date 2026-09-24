"""Regra: recusa importar de novo uma turma que já existe.

Sem ela, subir a mesma turma de novo criava turma, assignments e submissões duplicados, enquanto o
Parquet era gravado no MESMO diretório (o caminho vem do slug). Os assignments antigos, que carregam
os KCs, a Q-matrix aprovada e o modelo treinado, ficavam apontando para um Parquet cujo conteúdo
agora era outro. Nada disso dava erro.

A comparação é pelo SLUG, não pelo nome: "Turma 6" e "turma  6" são nomes diferentes e o MESMO
diretório. É uma parede explícita até existir re-treino com dados novos: falhar alto é melhor que
corromper em silêncio.
"""

from __future__ import annotations

from typing import Any

from api.assignments.domain.classroom_repository import ClassroomRepository
from api.assignments.domain.classroom_slug import ClassroomSlug


class ClassroomNotImportedYetRule:
    def __init__(self, classrooms: ClassroomRepository) -> None:
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
