# Assignment, uma lista de exercícios (por exemplo A439); a unidade de treino é um modelo por ele.

from __future__ import annotations

from dataclasses import dataclass

from api.assignments.domain.value_objects.assignment_status import AssignmentStatus


@dataclass
class Assignment:
    id: int | None  # None até ser gravado; o repositório devolve o id
    classroom_id: int
    name: str
    created_at: str
    status: AssignmentStatus | None = None
    progsnap_assignment_id: int | None = None  # o AssignmentID do dataset, distinto do id do banco
    published_model_id: int | None = None  # a versão de modelo que o dashboard usa
