"""Os repositórios SQLite de KCs, da Q-matrix e dos jobs de geração: ida e volta e transições."""

from __future__ import annotations

import pytest

from api.knowledge_components.domain.entities.kc_generation_job_entity import (
    KnowledgeComponentGenerationJob,
)
from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.entities.qmatrix_binding_entity import QMatrixBinding
from api.knowledge_components.infrastructure.repositories.sqlite_kc_generation_job_repository import (
    SqliteKnowledgeComponentGenerationJobRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_qmatrix_repository import (
    SqliteQMatrixRepository,
)
from api.shared.domain.value_objects.job_status import JobStatus


@pytest.fixture
def assignment_id(tmp_db) -> int:
    classroom_id = tmp_db.execute(
        "INSERT INTO classroom (name, created_at) VALUES ('T', 't0');"
    ).lastrowid
    return tmp_db.execute(
        "INSERT INTO assignment (classroom_id, name, created_at) VALUES (?, 'A', 't0');",
        (classroom_id,),
    ).lastrowid


def test_a_kc_round_trips_with_its_group_index(tmp_db, assignment_id):
    repository = SqliteKnowledgeComponentRepository(tmp_db)
    generated = KnowledgeComponent(id=None, assignment_id=assignment_id, name="laços", group_index=7)
    by_teacher = KnowledgeComponent(id=None, assignment_id=assignment_id, name="manual")

    generated.id = repository.add(generated)
    by_teacher.id = repository.add(by_teacher)

    assert repository.get(generated.id) == generated
    assert repository.get(by_teacher.id).group_index is None  # KC do professor: sem grupo
    assert repository.list_by_assignment(assignment_id) == [generated, by_teacher]


def test_rename_and_delete(tmp_db, assignment_id):
    repository = SqliteKnowledgeComponentRepository(tmp_db)
    kc_id = repository.add(KnowledgeComponent(id=None, assignment_id=assignment_id, name="a"))

    repository.rename(kc_id, "b")
    assert repository.get(kc_id).name == "b"
    repository.delete(kc_id)
    assert repository.get(kc_id) is None


def test_bindings_union_on_move_and_ignore_duplicates(tmp_db, assignment_id):
    kcs = SqliteKnowledgeComponentRepository(tmp_db)
    keep = kcs.add(KnowledgeComponent(id=None, assignment_id=assignment_id, name="keep"))
    drop = kcs.add(KnowledgeComponent(id=None, assignment_id=assignment_id, name="drop"))
    qmatrix = SqliteQMatrixRepository(tmp_db)
    qmatrix.bind_problems(assignment_id, keep, [1, 1])  # o duplicado é ignorado
    qmatrix.add(QMatrixBinding(id=None, assignment_id=assignment_id, kc_id=drop, problem_id=1))
    qmatrix.add(QMatrixBinding(id=None, assignment_id=assignment_id, kc_id=drop, problem_id=2))

    qmatrix.move_bindings(assignment_id, from_kc_id=drop, to_kc_id=keep)

    assert sorted(qmatrix.problems_of(keep)) == [1, 2]
    assert qmatrix.problems_of(drop) == []
    assert qmatrix.count_kcs_of_problem(assignment_id, 1) == 1


def test_a_generation_job_moves_through_its_states(tmp_db, assignment_id):
    jobs = SqliteKnowledgeComponentGenerationJobRepository(tmp_db)
    job_id = jobs.add(
        KnowledgeComponentGenerationJob(
            id=None, assignment_id=assignment_id, status=JobStatus.PENDING, created_at="t0"
        )
    )
    assert jobs.get(job_id).status is JobStatus.PENDING

    jobs.mark_running(job_id, started_at="t1")
    jobs.update_stage(job_id, "cluster", updated_at="t2")
    job = jobs.get(job_id)
    assert (job.status, job.stage, job.started_at) == (JobStatus.RUNNING, "cluster", "t1")

    jobs.mark_done(job_id, updated_at="t3")
    assert jobs.get(job_id).status is JobStatus.DONE

    jobs.mark_failed(job_id, "problema 7 ficaria com 0 KCs")
    assert jobs.get(job_id).error_message == "problema 7 ficaria com 0 KCs"
    assert jobs.get(999) is None
