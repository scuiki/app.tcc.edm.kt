"""Particionamento por aluno e o contrato split-before-vocab (CORE-04).

As duas funções aqui existem para a mesma garantia: o vocabulário de paths NUNCA pode observar
a partição de teste. `split_by_subject` separa por SubjectID (nenhum aluno atravessa as duas
partições) e `build_train_vocab` constrói o vocab só sobre os CodeStateIDs de treino — a
tensorização do held-out então produz OOV>0 por construção, que é a prova observável de que o
vazamento não aconteceu (T-01-05).
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
from sklearn.model_selection import train_test_split

from edmkt_core.features import build_vocab


def split_by_subject(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 1,  # Pitfall 3: TCC 1 partition uses random_state=1, NOT 42.
    min_attempts: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Partition events into train/test by student, disjoint by SubjectID.

    Extracted from tcc.edm.kt data_loader.load_spring2019_split (no CSV I/O, D-05):
    keep students with >= min_attempts Run.Program events, split the unique student
    set, then partition rows by membership so no SubjectID spans both partitions.
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


def build_train_vocab(
    cache_raw: dict[str, list[tuple[str, str, str]]],
    train_csids: Iterable[str],
) -> tuple[dict[str, int], dict[str, int]]:
    """Build the path vocabulary from the train partition's CodeStateIDs ONLY.

    The split-before-vocab contract (notebook 06 cell 14) promoted to code: subset
    the raw cache to train CodeStateIDs before calling build_vocab, so the vocab can
    never observe test-partition paths (CORE-04, T-01-05). Held-out tensorization
    then yields OOV>0 by construction.
    """
    train_csids = set(train_csids)
    cache_train = {c: cache_raw[c] for c in train_csids if c in cache_raw}
    return build_vocab(cache_train)
