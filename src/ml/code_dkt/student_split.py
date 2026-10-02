# Split treino/teste por aluno + vocabulário só do treino, para o teste nunca vazar no vocabulário.

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
from sklearn.model_selection import train_test_split

from ml.code_dkt.ast_paths import build_ast_path_vocabulary


def split_students_into_train_and_test(
    df: pd.DataFrame,
    *,
    progsnap_assignment_id: int,
    test_size: float = 0.2,
    random_state: int = 1,  # o random_state do repositório oficial, e não a seed 42 do treino
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Os alunos com Run.Program no exercício, na ordem das linhas e sem mínimo, como o repositório
    assignment_df = df[df["progsnap_assignment_id"] == progsnap_assignment_id]
    runs = assignment_df[assignment_df["event_type"] == "Run.Program"]
    students = pd.unique(runs["student_id"])
    train_s, test_s = train_test_split(
        students, test_size=test_size, random_state=random_state
    )

    train_df = assignment_df[assignment_df["student_id"].isin(train_s)].reset_index(drop=True)
    test_df = assignment_df[assignment_df["student_id"].isin(test_s)].reset_index(drop=True)
    return train_df, test_df


def build_train_only_vocabulary(
    ast_paths_by_snapshot: dict[str, list[tuple[str, str, str]]],
    train_snapshot_ids: Iterable[str],
) -> tuple[dict[str, int], dict[str, int]]:
    # O vocabulário de AST paths vem só dos snapshots de treino, com todos os paths de cada um.
    train_snapshot_ids = set(train_snapshot_ids)
    train_paths = {
        snapshot_id: ast_paths_by_snapshot[snapshot_id]
        for snapshot_id in train_snapshot_ids
        if snapshot_id in ast_paths_by_snapshot
    }
    return build_ast_path_vocabulary(train_paths)
