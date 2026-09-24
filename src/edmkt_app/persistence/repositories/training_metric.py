"""Série append-only de (época, loss) — a curva de treino (migração 0008)."""

from __future__ import annotations

import sqlite3
from typing import Optional


class TrainingMetricRepository:
    """Série append-only de (época, loss) por job — a curva de treino.

    O progresso corrente é DERIVADO da última linha, em vez de um campo mutável mantido em
    paralelo em training_job.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append(self, job_id: int, epoch: int, train_loss: float, recorded_at: str) -> None:
        # INSERT OR REPLACE: um re-treino que reaproveite o mesmo job_id sobrescreve a época em
        # vez de violar o UNIQUE(job_id, epoch).
        self._conn.execute(
            "INSERT OR REPLACE INTO training_metric (job_id, epoch, train_loss, recorded_at) "
            "VALUES (?, ?, ?, ?);",
            (job_id, epoch, train_loss, recorded_at),
        )

    def list_by_job(self, job_id: int) -> list[dict]:
        return [
            {"epoch": r["epoch"], "train_loss": r["train_loss"], "recorded_at": r["recorded_at"]}
            for r in self._conn.execute(
                "SELECT epoch, train_loss, recorded_at FROM training_metric "
                "WHERE job_id = ? ORDER BY epoch;",
                (job_id,),
            )
        ]

    def last(self, job_id: int) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT epoch, train_loss FROM training_metric WHERE job_id = ? "
            "ORDER BY epoch DESC LIMIT 1;",
            (job_id,),
        ).fetchone()
        return None if row is None else {"epoch": row["epoch"], "train_loss": row["train_loss"]}
