"""A divisão treino/teste por aluno, e o vocabulário construído só com o treino.

As duas funções existem para a mesma garantia: o vocabulário de AST paths NUNCA pode ver a
partição de teste. `split_students_into_train_and_test` separa por aluno (nenhum aluno fica nas
duas partições) e `build_train_only_vocabulary` monta o vocabulário só com os snapshots de treino.
A tensorização do teste então tem paths fora do vocabulário por construção, e essa é a prova
observável de que não houve vazamento.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
from sklearn.model_selection import train_test_split

from ml.code_dkt.ast_paths import build_ast_path_vocabulary


def split_students_into_train_and_test(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 1,  # a partição do TCC 1 usa random_state=1, NÃO a semente 42
    min_attempts: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Divide os eventos em treino/teste por aluno.

    Extraído do TCC 1 (data_loader.load_spring2019_split, sem ler CSV): mantém os alunos com
    pelo menos `min_attempts` eventos Run.Program, sorteia o conjunto de alunos e reparte as
    linhas por pertencimento, de modo que nenhum aluno aparece nas duas partições.
    """
    run = df[df["event_type"] == "Run.Program"]
    attempts = run.groupby("student_id").size()
    eligible = attempts[attempts >= min_attempts].index
    df_filtered = df[df["student_id"].isin(eligible)]

    students = df_filtered["student_id"].unique()
    train_s, test_s = train_test_split(
        students, test_size=test_size, random_state=random_state
    )

    train_df = df_filtered[df_filtered["student_id"].isin(train_s)].reset_index(drop=True)
    test_df = df_filtered[df_filtered["student_id"].isin(test_s)].reset_index(drop=True)
    return train_df, test_df


def build_train_only_vocabulary(
    ast_paths_by_snapshot: dict[str, list[tuple[str, str, str]]],
    train_snapshot_ids: Iterable[str],
) -> tuple[dict[str, int], dict[str, int]]:
    """O vocabulário de AST paths a partir SÓ dos snapshots de treino (notebook 06, célula 14)."""
    train_snapshot_ids = set(train_snapshot_ids)
    train_paths = {
        snapshot_id: ast_paths_by_snapshot[snapshot_id]
        for snapshot_id in train_snapshot_ids
        if snapshot_id in ast_paths_by_snapshot
    }
    return build_ast_path_vocabulary(train_paths)
