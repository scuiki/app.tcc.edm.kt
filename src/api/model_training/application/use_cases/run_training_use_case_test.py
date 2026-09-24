"""RunTrainingUseCase: a ordem arquivos → linha → publicação, e a curva gravada época por época.

Com fakes que registram as chamadas: nada de GPU, banco ou disco. A ordem importa porque publicar
antes de gravar exporia ao dashboard uma versão incompleta.
"""

from __future__ import annotations

import contextlib

import pandas as pd

from api.assignments.domain.entities.assignment_entity import Assignment, AssignmentStatus
from api.assignments.domain.entities.classroom_entity import Classroom
from api.model_training.application.use_cases.run_training_use_case import RunTrainingUseCase
from api.model_training.domain.value_objects.training_outcome import TrainingOutcome


class _Log(list):
    pass


class _Assignments:
    def __init__(self, log):
        self._log = log
        self._assignment = Assignment(
            id=7, classroom_id=1, name="A", created_at="t0",
            status=AssignmentStatus.KC_APPROVED, progsnap_assignment_id=439,
        )

    def get(self, assignment_id):
        return self._assignment

    def set_published_model(self, assignment_id, model_id):
        self._log.append(("publish", model_id))

    def set_status(self, assignment_id, status):
        self._log.append(("status", status))


class _Classrooms:
    def get(self, classroom_id):
        return Classroom(id=1, name="Turma X", created_at="t0")


class _CleanedSubmissions:
    def read(self, classroom_slug, progsnap_assignment_id):
        return pd.DataFrame({"event_type": ["Run.Program"]})


class _Trainer:
    total_epochs = 2

    def __init__(self, log):
        self._log = log

    def train(self, dataset, on_epoch):
        on_epoch(1, 0.9)
        on_epoch(2, 0.5)
        self._log.append(("train",))
        return TrainingOutcome(
            model=object(), vocab={}, hyperparameters={}, first_attempt_auc=0.73,
            java_parse_rate=0.95,
        )


class _ModelStore:
    def __init__(self, log):
        self._log = log

    def save(self, dataset, assignment_id, outcome):
        self._log.append(("save",))
        return 42


class _Jobs:
    def __init__(self, log):
        self._log = log

    def mark_running(self, job_id, total_epochs, started_at):
        self._log.append(("running", total_epochs))

    def mark_done(self, job_id, updated_at, java_parse_rate):
        self._log.append(("done", java_parse_rate))


class _EpochMetrics:
    def __init__(self, log):
        self._log = log

    def append(self, job_id, metric):
        self._log.append(("epoch", metric.epoch, metric.train_loss))


def _use_case(log) -> RunTrainingUseCase:
    return RunTrainingUseCase(
        assignments=_Assignments(log),
        classrooms=_Classrooms(),
        cleaned_submissions=_CleanedSubmissions(),
        trainer=_Trainer(log),
        model_store=_ModelStore(log),
        jobs=_Jobs(log),
        epoch_metrics=_EpochMetrics(log),
        unit_of_work=contextlib.nullcontext(),
    )


def test_the_version_is_published_only_after_it_is_saved():
    log = _Log()

    result = _use_case(log).execute(assignment_id=7, job_id=3)

    assert log == [
        ("running", 2),
        ("epoch", 1, 0.9),
        ("epoch", 2, 0.5),
        ("train",),
        ("save",),
        ("publish", 42),
        ("status", AssignmentStatus.TRAINED),
        ("done", 0.95),
    ]
    assert result == {"java_parse_rate": 0.95, "trained_model_id": 42, "first_attempt_auc": 0.73}
