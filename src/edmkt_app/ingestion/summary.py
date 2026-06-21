"""Resumo do dataset + preview da MainTable (INGEST-02).

Alimenta os cards de visão geral da tela de upload: contagens de alunos/assignments/problemas/
submissões derivadas do stream canônico, mais um preview das primeiras N linhas cruas da
MainTable para o professor confirmar que subiu o arquivo certo.

Módulo puro (DataFrame-in → dict/list-out): sem I/O, sem SQL, sem import de edmkt_core.
"""

from __future__ import annotations

import pandas as pd

# Colunas de metadados expostas no preview. O snapshot `Code` cru do aluno é DELIBERADAMENTE
# omitido: ele não agrega ao "confiro que subi o arquivo certo", incha o payload e é informação
# sensível atravessando a fronteira para o cliente (Information Disclosure — T-03-12).
PREVIEW_COLUMNS = [
    "SubjectID",
    "AssignmentID",
    "ProblemID",
    "EventType",
    "Score",
    "ServerTimestamp",
    "CodeStateID",
]


def build_summary(df: pd.DataFrame) -> dict:
    """Quatro contagens de visão geral (INGEST-02) sobre o stream canônico."""
    return {
        "n_students": int(df["SubjectID"].nunique()),
        "n_assignments": int(df["AssignmentID"].nunique()),
        "n_problems": int(df["ProblemID"].nunique()),
        "n_submissions": int(len(df)),
    }


def build_preview(main_df: pd.DataFrame, n: int = 10) -> list[dict]:
    """Primeiras `n` linhas cruas da MainTable como list[dict], SEM o snapshot `Code` cru.

    Só projeta as colunas de metadados existentes (PREVIEW_COLUMNS ∩ colunas presentes), então
    o `Code` nunca atravessa a fronteira para o cliente (T-03-12).
    """
    cols = [c for c in PREVIEW_COLUMNS if c in main_df.columns]
    return main_df.head(n)[cols].to_dict(orient="records")
