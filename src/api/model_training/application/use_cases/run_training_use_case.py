# Ordem arquivos -> linha -> publicação garante versão completa; o retorno do subprocess se perde.

from __future__ import annotations

from api.assignments.domain.entities.assignment_entity import AssignmentStatus
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.classroom_import.domain.interfaces.submission_repository import ISubmissionRepository
from api.model_training.domain.interfaces.code_dkt_trainer import ICodeDktTrainer
from api.model_training.domain.interfaces.trained_model_store import ITrainedModelStore
from api.model_training.domain.services.training_dataset_loading import load_training_dataset
from api.model_training.domain.entities.training_epoch_metric import TrainingEpochMetric
from api.model_training.domain.interfaces.training_epoch_metric_repository import (
    ITrainingEpochMetricRepository,
)
from api.model_training.domain.interfaces.training_job_repository import ITrainingJobRepository
from api.shared.application.services.clock import utc_now_iso
from api.shared.application.interfaces.unit_of_work import IUnitOfWork


class RunTrainingUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        submissions: ISubmissionRepository,
        trainer: ICodeDktTrainer,
        model_store: ITrainedModelStore,
        jobs: ITrainingJobRepository,
        epoch_metrics: ITrainingEpochMetricRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._submissions = submissions
        self._trainer = trainer
        self._model_store = model_store
        self._jobs = jobs
        self._epoch_metrics = epoch_metrics
        self._unit_of_work = unit_of_work

    def execute(self, assignment_id: int, job_id: int) -> dict:
        self._jobs.mark_running(job_id, self._trainer.total_epochs, started_at=utc_now_iso())
        dataset = load_training_dataset(
            assignment_id, self._assignments, self._submissions
        )

        def record_epoch(epoch: int, average_loss: float) -> None:
            # Append, não UPDATE (sobrescrever apagaria a curva); escrita curta sob WAL.
            self._epoch_metrics.append(
                job_id, TrainingEpochMetric(epoch, float(average_loss), utc_now_iso())
            )

        outcome = self._trainer.train(dataset, on_epoch=record_epoch)
        model_id = self._model_store.save(dataset, assignment_id, outcome)

        # Só agora a versão é publicada, um leitor nunca enxerga uma versão incompleta.
        with self._unit_of_work:
            self._assignments.set_published_model(assignment_id, model_id)
        self._assignments.set_status(assignment_id, AssignmentStatus.TRAINED)
        self._jobs.mark_done(job_id, utc_now_iso(), java_parse_rate=outcome.java_parse_rate)

        return {
            "java_parse_rate": outcome.java_parse_rate,
            "trained_model_id": model_id,
            "first_attempt_auc": outcome.first_attempt_auc,
        }
