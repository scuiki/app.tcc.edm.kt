"""Specifications: as regras que hoje são condicionais soltas dentro dos routers.

Cada teste prova a regra SEM subir HTTP — que é metade do ponto de extraí-las. O outro metade é
que a mensagem é a mesma de antes: mensagem e status code são contrato, e a suíte de API
(test_api_kc / test_api_training) segue como a rede que prova isso ponta a ponta.
"""

from __future__ import annotations

from dataclasses import dataclass


from edmkt_app import specs
from api.assignments.infrastructure.sqlite_classroom_repository import SqliteClassroomRepository
from api.assignments.infrastructure.sqlite_assignment_repository import SqliteAssignmentRepository
from api.assignments.domain.classroom_entity import Classroom
from api.assignments.domain.assignment_entity import Assignment


@dataclass
class _IngestDto:
    turma_name: str = ""


@dataclass
class _Dto:
    assignment_id: int = 0
    kc_keep: int = 0
    kc_drop: int = 0


def _assignment(conn, status: str) -> int:
    created = "2019-03-01T00:00:00+00:00"
    classroom_id = SqliteClassroomRepository(conn).add(
        Classroom(id=None, name="Turma X", created_at=created)
    )
    return SqliteAssignmentRepository(conn).add(
        Assignment(
            id=None,
            classroom_id=classroom_id,
            name="Assignment 439",
            published_model_id=None,
            created_at=created,
            status=status,
            progsnap_assignment_id=439,
        )
    )


TRAINING_SPEC = specs.AssignmentInStatus(
    allowed=("kc_approved",), message="Q-matrix ainda não aprovada pelo professor"
)


def test_assignment_in_status_passes_when_status_matches(tmp_db):
    dto = _Dto(assignment_id=_assignment(tmp_db, "kc_approved"))

    assert TRAINING_SPEC.check(tmp_db, dto) is None


def test_assignment_in_status_refuses_wrong_status(tmp_db):
    dto = _Dto(assignment_id=_assignment(tmp_db, "ready_for_kc_generation"))

    assert TRAINING_SPEC.check(tmp_db, dto) == "Q-matrix ainda não aprovada pelo professor"


def test_assignment_in_status_refuses_missing_assignment_with_the_same_message(tmp_db):
    # Conflação HERDADA de api/training.py: id inexistente devolve a mensagem de status errado,
    # não um "não existe". Preservada de propósito — separar mudaria 409 para 404 (contrato).
    assert TRAINING_SPEC.check(tmp_db, _Dto(assignment_id=99999)) == (
        "Q-matrix ainda não aprovada pelo professor"
    )


