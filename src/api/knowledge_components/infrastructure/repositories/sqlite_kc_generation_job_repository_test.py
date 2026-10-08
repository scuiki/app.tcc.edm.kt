# O progresso do job de KCs, gravado a cada item e zerado quando o estágio muda
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


def _job(conn) -> tuple[SqliteKnowledgeComponentGenerationJobRepository, int]:
    assignment_id = add_assignment(conn, add_classroom(conn))
    jobs = SqliteKnowledgeComponentGenerationJobRepository(conn)
    job_id = jobs.add(
        KnowledgeComponentGenerationJob(
            id=None, assignment_id=assignment_id, status=JobStatus.PENDING, created_at=CREATED
        )
    )
    return jobs, job_id


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

    jobs.record_generation_model(job_id, "claude-sonnet-5-5", "kcgen-v2")

    job = jobs.get(job_id)
    assert (job.model_id, job.prompt_version) == ("claude-sonnet-5-5", "kcgen-v2")
