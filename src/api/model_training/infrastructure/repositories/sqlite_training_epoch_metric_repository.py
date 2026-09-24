# ITrainingEpochMetricRepository sobre SQLite (`training_metric`), append-only; progresso derivado.

from __future__ import annotations

import sqlite3

from api.model_training.domain.entities.training_epoch_metric import TrainingEpochMetric


class SqliteTrainingEpochMetricRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append(self, job_id: int, metric: TrainingEpochMetric) -> None:
        # OR REPLACE, um re-treino que reaproveite o job_id sobrescreve em vez de violar o UNIQUE.
        self._conn.execute(
            "INSERT OR REPLACE INTO training_metric (job_id, epoch, train_loss, recorded_at) "
            "VALUES (?, ?, ?, ?);",
            (job_id, metric.epoch, metric.train_loss, metric.recorded_at),
        )

    def list_by_job(self, job_id: int) -> list[TrainingEpochMetric]:
        rows = self._conn.execute(
            "SELECT epoch, train_loss, recorded_at FROM training_metric WHERE job_id = ? "
            "ORDER BY epoch;",
            (job_id,),
        )
        return [TrainingEpochMetric(r["epoch"], r["train_loss"], r["recorded_at"]) for r in rows]

    def last(self, job_id: int) -> TrainingEpochMetric | None:
        row = self._conn.execute(
            "SELECT epoch, train_loss, recorded_at FROM training_metric WHERE job_id = ? "
            "ORDER BY epoch DESC LIMIT 1;",
            (job_id,),
        ).fetchone()
        return None if row is None else TrainingEpochMetric(
            row["epoch"], row["train_loss"], row["recorded_at"]
        )
