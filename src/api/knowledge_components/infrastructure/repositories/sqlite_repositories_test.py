# Repositórios SQLite de KCs, dos vínculos com problemas e dos jobs de geração.
from __future__ import annotations

import pytest

from api.knowledge_components.domain.entities.kc_generation_job_entity import (
    KnowledgeComponentGenerationJob,
)
from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.infrastructure.repositories.sqlite_kc_generation_job_repository import (
    SqliteKnowledgeComponentGenerationJobRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_problem_knowledge_component_repository import (
    SqliteProblemKnowledgeComponentRepository,
)
from api.shared.domain.value_objects.job_status import JobStatus
from tests.fixtures.assignments import add_assignment
from tests.fixtures.classrooms import add_classroom
from tests.fixtures.problems import add_problems


@pytest.fixture
def assignment_id(tmp_db) -> int:
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    add_problems(tmp_db, assignment_id, [1, 2])  # os problemas que os testes ligam aos KCs
    return assignment_id


def test_a_kc_round_trips_with_its_group_index_and_generated_name(tmp_db, assignment_id):
    repository = SqliteKnowledgeComponentRepository(tmp_db)
    generated = KnowledgeComponent(
        id=None, assignment_id=assignment_id, name="Laços", group_index=7, generated_name="loops"
    )
    by_teacher = KnowledgeComponent(id=None, assignment_id=assignment_id, name="manual")

    generated.id = repository.add(generated)
    by_teacher.id = repository.add(by_teacher)

    assert repository.get(generated.id) == generated
    # O KC do professor fica sem grupo e sem nome gerado
    assert (repository.get(by_teacher.id).group_index, repository.get(by_teacher.id).generated_name) == (
        None,
        None,
    )
    assert repository.list_by_assignment(assignment_id) == [generated, by_teacher]


def test_rename_and_remove_keeps_the_row_as_history(tmp_db, assignment_id):
    repository = SqliteKnowledgeComponentRepository(tmp_db)
    kc_id = repository.add(KnowledgeComponent(id=None, assignment_id=assignment_id, name="a"))
    assert repository.get(kc_id).updated_at is None

    repository.rename(kc_id, "b", "t1")
    renamed = repository.get(kc_id)
    assert (renamed.name, renamed.updated_at) == ("b", "t1")
    assert repository.list_by_assignment(assignment_id)[0].updated_at == "t1"
    repository.remove(kc_id, "t2")

    assert repository.get(kc_id) is None
    assert repository.list_by_assignment(assignment_id) == []
    row = tmp_db.execute(
        "SELECT name, updated_at, deleted_at FROM kc WHERE id = ?;", (kc_id,)
    ).fetchone()
    # A linha fica, só marcada como removida, e a remoção não conta como edição do nome
    assert tuple(row) == ("b", "t1", "t2")


def test_binding_the_same_problem_twice_keeps_one_active_link(tmp_db, assignment_id):
    kc_id = SqliteKnowledgeComponentRepository(tmp_db).add(
        KnowledgeComponent(id=None, assignment_id=assignment_id, name="k")
    )
    problem_kcs = SqliteProblemKnowledgeComponentRepository(tmp_db)

    problem_kcs.bind_problems(assignment_id, kc_id, [1, 1])

    assert problem_kcs.problems_of(kc_id) == [1]
    assert problem_kcs.count_kcs_of_problem(assignment_id, 1) == 1


def test_removing_a_link_hides_it_and_relinking_creates_a_new_row(tmp_db, assignment_id):
    kc_id = SqliteKnowledgeComponentRepository(tmp_db).add(
        KnowledgeComponent(id=None, assignment_id=assignment_id, name="k")
    )
    problem_kcs = SqliteProblemKnowledgeComponentRepository(tmp_db)
    problem_kcs.bind_problems(assignment_id, kc_id, [1])

    assert problem_kcs.remove(assignment_id, kc_id, 1, "t1") is True
    assert problem_kcs.remove(assignment_id, kc_id, 1, "t2") is False  # já não havia ativo
    assert problem_kcs.is_linked(assignment_id, kc_id, 1) is False
    assert problem_kcs.list_by_assignment(assignment_id) == []
    assert problem_kcs.count_kcs_of_problem(assignment_id, 1) == 0

    problem_kcs.bind_problems(assignment_id, kc_id, [1])

    assert problem_kcs.is_linked(assignment_id, kc_id, 1) is True
    rows = tmp_db.execute(
        "SELECT deleted_at FROM problem_kc WHERE kc_id = ? ORDER BY id;", (kc_id,)
    ).fetchall()
    assert [r[0] for r in rows] == ["t1", None]


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


def test_renaming_a_concept_keeps_its_generated_name(tmp_db, assignment_id):
    # O professor muda só o nome mostrado, e o nome gerado fica como registro do método
    repository = SqliteKnowledgeComponentRepository(tmp_db)
    kc_id = repository.add(
        KnowledgeComponent(
            id=None, assignment_id=assignment_id, name="Laço for", generated_name="for loop"
        )
    )

    repository.rename(kc_id, "Laços", "t1")

    renamed = repository.get(kc_id)
    assert (renamed.name, renamed.generated_name, renamed.updated_at) == ("Laços", "for loop", "t1")
