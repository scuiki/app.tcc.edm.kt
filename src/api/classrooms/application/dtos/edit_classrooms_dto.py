# Pedidos e respostas de criar, renomear e excluir uma turma.

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, StringConstraints

# O nome sem espaços nas pontas, e um nome em branco é recusado com 422
ClassroomName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]


class CreateClassroomDTO(BaseModel):
    name: ClassroomName


class RenameClassroomBody(BaseModel):
    name: ClassroomName


class RenameClassroomDTO(BaseModel):
    classroom_id: int
    name: ClassroomName


class RemoveClassroomDTO(BaseModel):
    classroom_id: int


class ClassroomDTO(BaseModel):
    id: int
    name: str
    created_at: str


class RemovedClassroomDTO(BaseModel):
    deleted_classroom_id: int
