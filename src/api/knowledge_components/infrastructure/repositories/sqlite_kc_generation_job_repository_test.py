# O progresso do job de KCs, gravado a cada item e zerado a cada estágio, e o último job concluído
from __future__ import annotations

from api.knowledge_components.domain.entities.kc_generation_job_entity import (
    KnowledgeComponentGenerationJob,
)
from api.knowledge_components.infrastructure.repositories.sqlite_kc_generation_job_repository import (
    SqliteKnowledgeComponentGenerationJobRepository,
)
from api.shared.domain.value_objects.job_status import JobStatus
from tests.fixtures.assignments import add_assignment
from tests.fixtures.classrooms import add_classroom

CREATED = "2026-09-25T00:00:00Z"


def _add_job(jobs: SqliteKnowledgeComponentGenerationJobRepository, assignment_id: int) -> int:
    return jobs.add(
        KnowledgeComponentGenerationJob(
            id=None, assignment_id=assignment_id, status=JobStatus.PENDING, created_at=CREATED
        )
    )


def _job(conn) -> tuple[SqliteKnowledgeComponentGenerationJobRepository, int]:
    assignment_id = add_assignment(conn, add_classroom(conn))
    jobs = SqliteKnowledgeComponentGenerationJobRepository(conn)
    return jobs, _add_job(jobs, assignment_id)


def _done_job(jobs, assignment_id: int, finished_at: str) -> int:
    job_id = _add_job(jobs, assignment_id)
    jobs.mark_running(job_id, started_at=CREATED)
    jobs.mark_done(job_id, finished_at)
    return job_id


def test_a_new_job_has_no_progress(tmp_db):
    jobs, job_id = _job(tmp_db)
    job = jobs.get(job_id)
    assert (job.progress_done, job.progress_total) == (None, None)


def test_progress_is_saved_item_by_item(tmp_db):
    jobs, job_id = _job(tmp_db)
    jobs.update_stage(job_id, "generate", CREATED)
    jobs.update_progress(job_id, 7, 10, CREATED)
    job = jobs.get(job_id)
    assert (job.stage, job.progress_done, job.progress_total) == ("generate", 7, 10)


def test_a_new_stage_starts_without_the_progress_of_the_previous_one(tmp_db):
    jobs, job_id = _job(tmp_db)
    jobs.update_stage(job_id, "generate", CREATED)
    jobs.update_progress(job_id, 10, 10, CREATED)
    jobs.update_stage(job_id, "cluster", CREATED)
    job = jobs.get(job_id)
    assert (job.stage, job.progress_done, job.progress_total) == ("cluster", None, None)


def test_the_job_records_the_model_and_the_prompt_version(tmp_db):
    jobs, job_id = _job(tmp_db)
    assert (jobs.get(job_id).model_id, jobs.get(job_id).prompt_version) == (None, None)

    jobs.record_generation_model(job_id, "claude-haiku-4-5-20251001", "kcgen-v2")

    job = jobs.get(job_id)
    assert (job.model_id, job.prompt_version) == ("claude-haiku-4-5-20251001", "kcgen-v2")


def test_an_assignment_without_jobs_has_no_done_job(tmp_db):
    jobs = SqliteKnowledgeComponentGenerationJobRepository(tmp_db)

    assert jobs.find_latest_done(add_assignment(tmp_db, add_classroom(tmp_db))) is None


def test_the_latest_done_job_ignores_the_running_and_the_failed_ones(tmp_db):
    # Os dois têm data mais nova que a do concluído, e só a situação os separa
    jobs = SqliteKnowledgeComponentGenerationJobRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    done_id = _done_job(jobs, assignment_id, "2026-10-07T02:30:00Z")
    running_id = _add_job(jobs, assignment_id)
    jobs.mark_running(running_id, started_at="2026-10-08T09:00:00Z")
    jobs.update_stage(running_id, "generate", "2026-10-08T09:00:00Z")
    failed_id = _add_job(jobs, assignment_id)
    jobs.update_stage(failed_id, "cluster", "2026-10-08T10:00:00Z")
    jobs.mark_failed(failed_id, "falhou")

    latest = jobs.find_latest_done(assignment_id)

    assert (latest.id, latest.status, latest.updated_at) == (
        done_id,
        JobStatus.DONE,
        "2026-10-07T02:30:00Z",
    )


def test_the_latest_done_job_is_the_one_that_finished_last(tmp_db):
    # O job criado depois terminou antes, então a ordem é pela data, e não pelo id
    jobs = SqliteKnowledgeComponentGenerationJobRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    finished_last = _done_job(jobs, assignment_id, "2026-10-07T02:30:00Z")
    _done_job(jobs, assignment_id, "2026-10-06T10:00:00Z")

    assert jobs.find_latest_done(assignment_id).id == finished_last


def test_two_jobs_done_at_the_same_time_resolve_to_the_newest_one(tmp_db):
    jobs = SqliteKnowledgeComponentGenerationJobRepository(tmp_db)
    assignment_id = add_assignment(tmp_db, add_classroom(tmp_db))
    _done_job(jobs, assignment_id, "2026-10-07T02:30:00Z")
    newest = _done_job(jobs, assignment_id, "2026-10-07T02:30:00Z")

    assert jobs.find_latest_done(assignment_id).id == newest


def test_the_latest_done_job_ignores_other_assignments(tmp_db):
    jobs = SqliteKnowledgeComponentGenerationJobRepository(tmp_db)
    classroom_id = add_classroom(tmp_db)
    first = add_assignment(tmp_db, classroom_id, name="A")
    second = add_assignment(tmp_db, classroom_id, name="B")
    own = _done_job(jobs, first, "2026-10-06T10:00:00Z")
    _done_job(jobs, second, "2026-10-07T02:30:00Z")

    assert jobs.find_latest_done(first).id == own
