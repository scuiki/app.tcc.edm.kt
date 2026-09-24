"""As quatro contagens de visão geral do dado limpo, para os cards da tela de upload."""

from __future__ import annotations

import pandas as pd


def summarize_cleaned_submissions(df: pd.DataFrame) -> dict:
    """Alunos, assignments, problemas e submissões no dado limpo."""
    return {
        "n_students": int(df["student_id"].nunique()),
        "n_assignments": int(df["progsnap_assignment_id"].nunique()),
        "n_problems": int(df["problem_id"].nunique()),
        "n_submissions": int(len(df)),
    }

