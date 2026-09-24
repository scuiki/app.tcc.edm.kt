"""Os repositórios SQLite do treino: jobs, curva de loss e versões de modelo."""

from __future__ import annotations

import pytest

from api.model_training.domain.trained_model_entity import TrainedModel
from api.model_training.domain.training_epoch_metric import TrainingEpochMetric
from api.model_training.domain.training_job_entity import TrainingJob
from api.model_training.infrastructure.sqlite_trained_model_repository import (
    SqliteTrainedModelRepository,
)
from api.model_training.infrastructure.sqlite_training_epoch_metric_repository import (
    SqliteTrainingEpochMetricRepository,
)
from api.model_training.infrastructure.sqlite_training_job_repository import (
    SqliteTrainingJobRepository,
)
from api.shared.domain.job_status import JobStatus


@pytest.fixture
def assignment_id(tmp_db) -> int:
    classroom_id = tmp_db.execute(
        "INSERT INTO classroom (name, created_at) VALUES ('T', 't0');"
    ).lastrowid
    return tmp_db.execute(
        "INSERT INTO assignment (classroom_id, name, created_at) VALUES (?, 'A', 't0');",
        (classroom_id,),
    ).lastrowid


def test_a_training_job_moves_through_its_states(tmp_db, assignment_id):
    jobs = SqliteTrainingJobRepository(tmp_db)
    job_id = jobs.add(
        TrainingJob(id=None, assignment_id=assignment_id, status=JobStatus.PENDING, created_at="t0")
    )
    assert jobs.get(job_id) == TrainingJob(
        id=job_id, assignment_id=assignment_id, status=JobStatus.PENDING, created_at="t0"
    )

    jobs.mark_running(job_id, total_epochs=40, started_at="t1")
    assert (jobs.get(job_id).status, jobs.get(job_id).total_epochs) == (JobStatus.RUNNING, 40)

    jobs.mark_done(job_id, updated_at="t2", java_parse_rate=0.86)
    assert (jobs.get(job_id).status, jobs.get(job_id).java_parse_rate) == (JobStatus.DONE, 0.86)

    jobs.mark_failed(job_id, "boom")
    assert jobs.get(job_id).error_message == "boom"


def test_marking_done_without_a_parse_rate_keeps_the_one_already_recorded(tmp_db, assignment_id):
    jobs = SqliteTrainingJobRepository(tmp_db)
    job_id = jobs.add(
        TrainingJob(id=None, assignment_id=assignment_id, status=JobStatus.PENDING, created_at="t0")
    )
    jobs.mark_done(job_id, updated_at="t1", java_parse_rate=0.9)

    jobs.mark_done(job_id, updated_at="t2", java_parse_rate=None)

    assert jobs.get(job_id).java_parse_rate == 0.9


def test_the_loss_curve_is_append_only_and_ordered(tmp_db, assignment_id):
    job_id = SqliteTrainingJobRepository(tmp_db).add(
        TrainingJob(id=None, assignment_id=assignment_id, status=JobStatus.RUNNING, created_at="t0")
    )
    metrics = SqliteTrainingEpochMetricRepository(tmp_db)

    metrics.append(job_id, TrainingEpochMetric(2, 0.5, "t2"))
    metrics.append(job_id, TrainingEpochMetric(1, 0.9, "t1"))

    assert [m.epoch for m in metrics.list_by_job(job_id)] == [1, 2]
    assert metrics.last(job_id) == TrainingEpochMetric(2, 0.5, "t2")
    assert metrics.last(999) is None


def test_a_trained_model_references_its_files_by_path_never_by_bytes(tmp_db, assignment_id):
    models = SqliteTrainedModelRepository(tmp_db)
    new = TrainedModel(
        id=None, assignment_id=assignment_id, version_number=1, content_hash="h",
        model_dir="data/turma/models/1/v1", created_at="t0", first_attempt_auc=0.73,
        git_commit="abc", data_hash="def",
    )

    model_id = models.add(new)

    assert models.get(model_id) == TrainedModel(**{**new.__dict__, "id": model_id})
    assert models.next_version_number(assignment_id) == 2
    types = {r["name"]: r["type"] for r in tmp_db.execute("PRAGMA table_info(model_artifact);")}
    assert all(t.upper() != "BLOB" for t in types.values())
