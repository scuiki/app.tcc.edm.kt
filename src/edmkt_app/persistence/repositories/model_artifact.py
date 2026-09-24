"""Artefatos de modelo versionados, write-once, com AUC e proveniência."""

from __future__ import annotations

import sqlite3
from typing import Optional

from edmkt_app.persistence import models


class ModelArtifactRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, artifact: models.ModelArtifact) -> int:
        cur = self._conn.execute(
            "INSERT INTO model_artifact "
            "(assignment_id, version_number, content_hash, artifact_dir, created_at, first_attempt_auc, "
            "git_commit, data_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            (
                artifact.assignment_id,
                artifact.version_number,
                artifact.content_hash,
                artifact.artifact_dir,
                artifact.created_at,
                artifact.first_auc,
                artifact.git_commit,
                artifact.data_hash,
            ),
        )
        return cur.lastrowid

    def get(self, artifact_id: int) -> Optional[models.ModelArtifact]:
        row = self._conn.execute(
            "SELECT id, assignment_id, version_number, content_hash, artifact_dir, created_at, "
            "first_attempt_auc, git_commit, data_hash "
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
            first_auc=row["first_attempt_auc"],
            git_commit=row["git_commit"],
            data_hash=row["data_hash"],
        )
