"""TrainedModelRepository sobre SQLite (tabela `model_artifact`), mais o que o store usa ao gravar."""

from __future__ import annotations

import sqlite3

from api.model_training.domain.trained_model_entity import TrainedModel

_COLUMNS = (
    "id, assignment_id, version_number, content_hash, artifact_dir, created_at, "
    "first_attempt_auc, git_commit, data_hash"
)


def _to_entity(row: sqlite3.Row) -> TrainedModel:
    return TrainedModel(
        id=row["id"],
        assignment_id=row["assignment_id"],
        version_number=row["version_number"],
        content_hash=row["content_hash"],
        model_dir=row["artifact_dir"],
        created_at=row["created_at"],
        first_attempt_auc=row["first_attempt_auc"],
        git_commit=row["git_commit"],
        data_hash=row["data_hash"],
    )


class SqliteTrainedModelRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, trained_model: TrainedModel) -> int:
        cur = self._conn.execute(
            "INSERT INTO model_artifact (assignment_id, version_number, content_hash, "
            "artifact_dir, created_at, first_attempt_auc, git_commit, data_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            (
                trained_model.assignment_id,
                trained_model.version_number,
                trained_model.content_hash,
                trained_model.model_dir,
                trained_model.created_at,
                trained_model.first_attempt_auc,
                trained_model.git_commit,
                trained_model.data_hash,
            ),
        )
        return cur.lastrowid

    def get(self, model_id: int) -> TrainedModel | None:
        row = self._conn.execute(
            f"SELECT {_COLUMNS} FROM model_artifact WHERE id = ?;", (model_id,)
        ).fetchone()
        return None if row is None else _to_entity(row)

    def next_version_number(self, assignment_id: int) -> int:
        """MAX(version_number) + 1 no assignment. O UNIQUE(assignment_id, version_number) é a rede
        contra dois treinos calculando o mesmo número (a trava de job já impede os dois)."""
        row = self._conn.execute(
            "SELECT COALESCE(MAX(version_number), 0) + 1 AS next FROM model_artifact "
            "WHERE assignment_id = ?;",
            (assignment_id,),
        ).fetchone()
        return int(row["next"])
