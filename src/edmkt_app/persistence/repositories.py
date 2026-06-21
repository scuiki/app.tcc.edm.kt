"""Repositórios por entidade: round-trip linha↔dataclass à mão sobre sqlite3 puro (D-03/SC4).

Uma classe-repo por entidade recebe a conexão e expõe insert(obj) -> int (via cursor.lastrowid
em vez da cláusula pós-3.35 — Pitfall 7, o SQLite do container pode ser pré-3.35) e
get(id) -> dataclass | None.
TODO SQL é parametrizado com placeholders ? (V5/T-02-04); nenhum dado é interpolado em string.

Escopo: round-trip básico das 8 entidades. A versão monótona do ModelArtifact (Pattern 2) e o
flip do current_version_id vivem em 02-04, não aqui.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from edmkt_app.persistence import models


class TurmaRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, turma: models.Turma) -> int:
        cur = self._conn.execute(
            "INSERT INTO turma (name, created_at) VALUES (?, ?);",
            (turma.name, turma.created_at),
        )
        return cur.lastrowid

    def get(self, turma_id: int) -> Optional[models.Turma]:
        row = self._conn.execute(
            "SELECT id, name, created_at FROM turma WHERE id = ?;", (turma_id,)
        ).fetchone()
        if row is None:
            return None
        return models.Turma(id=row["id"], name=row["name"], created_at=row["created_at"])


class AssignmentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, assignment: models.Assignment) -> int:
        cur = self._conn.execute(
            "INSERT INTO assignment (turma_id, name, current_version_id, created_at, status) "
            "VALUES (?, ?, ?, ?, ?);",
            (
                assignment.turma_id,
                assignment.name,
                assignment.current_version_id,
                assignment.created_at,
                assignment.status,
            ),
        )
        return cur.lastrowid

    def get(self, assignment_id: int) -> Optional[models.Assignment]:
        row = self._conn.execute(
            "SELECT id, turma_id, name, current_version_id, created_at, status "
            "FROM assignment WHERE id = ?;",
            (assignment_id,),
        ).fetchone()
        if row is None:
            return None
        return models.Assignment(
            id=row["id"],
            turma_id=row["turma_id"],
            name=row["name"],
            current_version_id=row["current_version_id"],
            created_at=row["created_at"],
            status=row["status"],
        )


class SubmissionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, submission: models.Submission) -> int:
        cur = self._conn.execute(
            "INSERT INTO submission "
            "(assignment_id, code_state_id, subject_id, problem_id, score, created_at, event_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?);",
            (
                submission.assignment_id,
                submission.code_state_id,
                submission.subject_id,
                submission.problem_id,
                submission.score,
                submission.created_at,
                submission.event_type,
            ),
        )
        return cur.lastrowid

    def get(self, submission_id: int) -> Optional[models.Submission]:
        row = self._conn.execute(
            "SELECT id, assignment_id, code_state_id, subject_id, problem_id, score, "
            "created_at, event_type "
            "FROM submission WHERE id = ?;",
            (submission_id,),
        ).fetchone()
        if row is None:
            return None
        return models.Submission(
            id=row["id"],
            assignment_id=row["assignment_id"],
            code_state_id=row["code_state_id"],
            subject_id=row["subject_id"],
            problem_id=row["problem_id"],
            score=row["score"],
            created_at=row["created_at"],
            event_type=row["event_type"],
        )


class KCRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, kc: models.KC) -> int:
        cur = self._conn.execute(
            "INSERT INTO kc (assignment_id, name) VALUES (?, ?);",
            (kc.assignment_id, kc.name),
        )
        return cur.lastrowid

    def get(self, kc_id: int) -> Optional[models.KC]:
        row = self._conn.execute(
            "SELECT id, assignment_id, name FROM kc WHERE id = ?;", (kc_id,)
        ).fetchone()
        if row is None:
            return None
        return models.KC(id=row["id"], assignment_id=row["assignment_id"], name=row["name"])


class QMatrixRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, qmatrix: models.QMatrix) -> int:
        cur = self._conn.execute(
            "INSERT INTO qmatrix (assignment_id, kc_id, problem_id) VALUES (?, ?, ?);",
            (qmatrix.assignment_id, qmatrix.kc_id, qmatrix.problem_id),
        )
        return cur.lastrowid

    def get(self, qmatrix_id: int) -> Optional[models.QMatrix]:
        row = self._conn.execute(
            "SELECT id, assignment_id, kc_id, problem_id FROM qmatrix WHERE id = ?;",
            (qmatrix_id,),
        ).fetchone()
        if row is None:
            return None
        return models.QMatrix(
            id=row["id"],
            assignment_id=row["assignment_id"],
            kc_id=row["kc_id"],
            problem_id=row["problem_id"],
        )


class ModelArtifactRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, artifact: models.ModelArtifact) -> int:
        cur = self._conn.execute(
            "INSERT INTO model_artifact "
            "(assignment_id, version_number, content_hash, artifact_dir, created_at) "
            "VALUES (?, ?, ?, ?, ?);",
            (
                artifact.assignment_id,
                artifact.version_number,
                artifact.content_hash,
                artifact.artifact_dir,
                artifact.created_at,
            ),
        )
        return cur.lastrowid

    def get(self, artifact_id: int) -> Optional[models.ModelArtifact]:
        row = self._conn.execute(
            "SELECT id, assignment_id, version_number, content_hash, artifact_dir, created_at "
            "FROM model_artifact WHERE id = ?;",
            (artifact_id,),
        ).fetchone()
        if row is None:
            return None
        return models.ModelArtifact(
            id=row["id"],
            assignment_id=row["assignment_id"],
            version_number=row["version_number"],
            content_hash=row["content_hash"],
            artifact_dir=row["artifact_dir"],
            created_at=row["created_at"],
        )


class MasteryPredictionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, prediction: models.MasteryPrediction) -> int:
        cur = self._conn.execute(
            "INSERT INTO mastery_prediction "
            "(model_artifact_id, subject_id, kc_id, mastery) VALUES (?, ?, ?, ?);",
            (
                prediction.model_artifact_id,
                prediction.subject_id,
                prediction.kc_id,
                prediction.mastery,
            ),
        )
        return cur.lastrowid

    def get(self, prediction_id: int) -> Optional[models.MasteryPrediction]:
        row = self._conn.execute(
            "SELECT id, model_artifact_id, subject_id, kc_id, mastery "
            "FROM mastery_prediction WHERE id = ?;",
            (prediction_id,),
        ).fetchone()
        if row is None:
            return None
        return models.MasteryPrediction(
            id=row["id"],
            model_artifact_id=row["model_artifact_id"],
            subject_id=row["subject_id"],
            kc_id=row["kc_id"],
            mastery=row["mastery"],
        )


class TrainingJobRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, job: models.TrainingJob) -> int:
        cur = self._conn.execute(
            "INSERT INTO training_job (assignment_id, status, created_at) VALUES (?, ?, ?);",
            (job.assignment_id, job.status, job.created_at),
        )
        return cur.lastrowid

    def get(self, job_id: int) -> Optional[models.TrainingJob]:
        row = self._conn.execute(
            "SELECT id, assignment_id, status, created_at, current_epoch, total_epochs, "
            "train_loss, started_at, updated_at, error_message FROM training_job WHERE id = ?;",
            (job_id,),
        ).fetchone()
        if row is None:
            return None
        return models.TrainingJob(
            id=row["id"],
            assignment_id=row["assignment_id"],
            status=row["status"],
            created_at=row["created_at"],
            current_epoch=row["current_epoch"],
            total_epochs=row["total_epochs"],
            train_loss=row["train_loss"],
            started_at=row["started_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"],
        )

    def update_progress(
        self, job_id: int, current_epoch: int, train_loss: float, updated_at: str
    ) -> None:
        self._conn.execute(
            "UPDATE training_job SET current_epoch = ?, train_loss = ?, updated_at = ? WHERE id = ?;",
            (current_epoch, train_loss, updated_at, job_id),
        )

    def mark_running(self, job_id: int, total_epochs: int, started_at: str) -> None:
        self._conn.execute(
            "UPDATE training_job SET status = 'running', total_epochs = ?, started_at = ? WHERE id = ?;",
            (total_epochs, started_at, job_id),
        )

    def mark_done(self, job_id: int, updated_at: str) -> None:
        self._conn.execute(
            "UPDATE training_job SET status = 'done', updated_at = ? WHERE id = ?;",
            (updated_at, job_id),
        )

    def mark_failed(self, job_id: int, error_message: str) -> None:
        self._conn.execute(
            "UPDATE training_job SET status = 'failed', error_message = ? WHERE id = ?;",
            (error_message, job_id),
        )
