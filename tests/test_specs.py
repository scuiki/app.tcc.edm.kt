"""Specifications: as regras que hoje são condicionais soltas dentro dos routers.

Cada teste prova a regra SEM subir HTTP — que é metade do ponto de extraí-las. O outro metade é
que a mensagem é a mesma de antes: mensagem e status code são contrato, e a suíte de API
(test_api_kc / test_api_training) segue como a rede que prova isso ponta a ponta.
"""

from __future__ import annotations

from dataclasses import dataclass


from edmkt_app import specs
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
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


def test_assignment_is_draft_reports_the_current_status(tmp_db):
    dto = _Dto(assignment_id=_assignment(tmp_db, "ready_for_kc_generation"))

    assert specs.AssignmentIsDraft().check(tmp_db, dto) == (
        "assignment não está em kc_draft (status atual: ready_for_kc_generation)"
    )


def test_assignment_is_draft_stays_silent_when_the_assignment_is_missing(tmp_db):
    # Autossuficiência: como TODAS as specs rodam, esta não pode estourar quando o alvo não
    # existe — inexistência é NotFound, levantado antes, e não regra violada.
    assert specs.AssignmentIsDraft().check(tmp_db, _Dto(assignment_id=99999)) is None


def test_assignment_has_kcs_refuses_an_empty_draft(tmp_db):
    dto = _Dto(assignment_id=_assignment(tmp_db, "kc_draft"))

    assert specs.AssignmentHasKCs().check(tmp_db, dto) == (
        "assignment não tem nenhum KC para aprovar"
    )


def test_assignment_has_kcs_passes_with_at_least_one(tmp_db):
    assignment_id = _assignment(tmp_db, "kc_draft")
    repos.KCRepository(tmp_db).insert(
        models.KC(id=None, assignment_id=assignment_id, name="Laços", kc_index=0)
    )

    assert specs.AssignmentHasKCs().check(tmp_db, _Dto(assignment_id=assignment_id)) is None


def test_kcs_are_distinct_refuses_self_merge(tmp_db):
    assert specs.KCsAreDistinct().check(tmp_db, _Dto(kc_keep=7, kc_drop=7)) == (
        "kc_keep e kc_drop são o mesmo KC"
    )


def test_kcs_belong_to_assignment_refuses_a_kc_from_another_assignment(tmp_db):
    a1 = _assignment(tmp_db, "kc_draft")
    a2 = SqliteAssignmentRepository(tmp_db).add(
        Assignment(
            id=None,
            classroom_id=1,
            name="Assignment 487",
            published_model_id=None,
            created_at="2019-03-01T00:00:00+00:00",
            status="kc_draft",
        )
    )
    kc_repo = repos.KCRepository(tmp_db)
    keep = kc_repo.insert(models.KC(id=None, assignment_id=a1, name="A", kc_index=0))
    alheio = kc_repo.insert(models.KC(id=None, assignment_id=a2, name="B", kc_index=0))

    dto = _Dto(assignment_id=a1, kc_keep=keep, kc_drop=alheio)
    assert specs.KCsBelongToAssignment().check(tmp_db, dto) == "KC não pertence ao assignment"


def test_kcs_belong_to_assignment_passes_when_both_are_local(tmp_db):
    a1 = _assignment(tmp_db, "kc_draft")
    kc_repo = repos.KCRepository(tmp_db)
    keep = kc_repo.insert(models.KC(id=None, assignment_id=a1, name="A", kc_index=0))
    drop = kc_repo.insert(models.KC(id=None, assignment_id=a1, name="B", kc_index=1))

    dto = _Dto(assignment_id=a1, kc_keep=keep, kc_drop=drop)
    assert specs.KCsBelongToAssignment().check(tmp_db, dto) is None


