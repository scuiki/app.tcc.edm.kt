"""A resposta de GET /assignments: os assignments com os DOIS ids, o do banco e o do dataset."""

from __future__ import annotations

from pydantic import BaseModel

from api.assignments.domain.entities.assignment_entity import AssignmentStatus


class AssignmentSummaryDTO(BaseModel):
    id: int  # o id do banco
    progsnap_assignment_id: int | None  # o AssignmentID do dataset (ex.: 439)
    name: str
    status: AssignmentStatus | None
    published_model_id: int | None  # None até existir um modelo publicado


class ListAssignmentsResponseDTO(BaseModel):
    assignments: list[AssignmentSummaryDTO]
