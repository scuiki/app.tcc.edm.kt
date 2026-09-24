# A resposta de GET /classrooms, cada turma com as contagens e a situação dela.

from __future__ import annotations

from pydantic import BaseModel

from api.classrooms.domain.value_objects.classroom_status import ClassroomStatus


class ClassroomSummaryDTO(BaseModel):
    id: int
    name: str
    created_at: str
    problem_count: int
    student_count: int
    status: ClassroomStatus


class ListClassroomsResponseDTO(BaseModel):
    classrooms: list[ClassroomSummaryDTO]
