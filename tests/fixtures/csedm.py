# O CSEDM real dos testes de regressão e de comparação com o paper, carregado uma vez por sessão.

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import pytest

from api.classroom_import.domain.services.submission_cleaning import PROGSNAP_TO_CLEANED_COLUMNS


def resolve_csedm_path() -> Path:
    # Resolve EDMKT_CSEDM_PATH ou pula o teste; o CSEDM real nunca é copiado pro repo, só apontado.
    raw = os.environ.get("EDMKT_CSEDM_PATH")
    if not raw:
        pytest.skip(
            "EDMKT_CSEDM_PATH não está definida, e o teste com o CSEDM real foi pulado. "
            "Aponte para o diretório da CSEDM, com MainTable.csv e CodeStates/, para rodar."
        )
    data_dir = Path(raw)
    if not (data_dir / "MainTable.csv").exists():
        pytest.skip(f"EDMKT_CSEDM_PATH={data_dir} não tem MainTable.csv, e o teste foi pulado.")
    return data_dir


@pytest.fixture(scope="session")
def csedm_main_table() -> pd.DataFrame:
    # Todos os exercícios, e cada teste escolhe o seu pela partição, como o repositório oficial

    # Fora do hash 0 os AST paths não saem na ordem do app e o AUC não se compara, falha sem pular
    assert sys.flags.hash_randomization == 0, (
        "PYTHONHASHSEED não é 0 neste processo, e os AST paths não saem na ordem que o app fixa"
    )
    data_dir = resolve_csedm_path()

    df = pd.read_csv(data_dir / "MainTable.csv")
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True, errors="coerce")
    df["AssignmentID"] = pd.to_numeric(df["AssignmentID"], errors="coerce").astype("Int64")
    df["ProblemID"] = pd.to_numeric(df["ProblemID"], errors="coerce").astype("Int64")

    # Só Run.Program + label binário (o filtro exato que o TCC 1 usou pra treinar o Code-DKT).
    df = df[df["EventType"] == "Run.Program"].copy()
    df["correct"] = (df["Score"] == 1.0).astype(int)

    # Junta o snapshot Java por evento (CodeStateID -> Code), pro seam ver código inline.
    code_states = pd.read_csv(data_dir / "CodeStates" / "CodeStates.csv")
    code_map = dict(zip(code_states["CodeStateID"].astype(str), code_states["Code"].fillna("")))
    df["Code"] = df["CodeStateID"].astype(str).map(code_map).fillna("")

    # Mesma tradução que a importação aplica; daqui em diante, nomes do glossário.
    df = df.rename(columns={**PROGSNAP_TO_CLEANED_COLUMNS, "correct": "is_correct"})
    return df.reset_index(drop=True)
