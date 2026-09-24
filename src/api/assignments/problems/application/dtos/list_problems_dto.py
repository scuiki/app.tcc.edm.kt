# A resposta de GET /assignments/{assignment_id}/problems.

from __future__ import annotations

from pydantic import BaseModel


class ProblemDTO(BaseModel):
    problem_id: int  # o ProblemID do dataset
    description: str | None  # vazia até a geração de KCs


class ListProblemsResponseDTO(BaseModel):
    assignment_id: int
    problems: list[ProblemDTO]
