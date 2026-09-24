"""Resumo do dataset (INGEST-02).

Alimenta os cards de visão geral da tela de upload: contagens de alunos/assignments/problemas/
submissões derivadas do stream canônico.

Módulo puro (DataFrame-in → dict/list-out): sem I/O, sem SQL, sem import de ml.
"""

from __future__ import annotations

import pandas as pd


def build_summary(df: pd.DataFrame) -> dict:
    """Quatro contagens de visão geral (INGEST-02) sobre o stream canônico."""
    return {
        "n_students": int(df["student_id"].nunique()),
        "n_assignments": int(df["progsnap_assignment_id"].nunique()),
        "n_problems": int(df["problem_id"].nunique()),
        "n_submissions": int(len(df)),
    }

