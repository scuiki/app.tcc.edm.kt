"""Lê as tabelas CSV do ProgSnap2 do professor, sem confiar nos tipos que vierem.

O pré-voo de falhas duras: o CSEDM é bem-comportado, um upload real não. Lê o MainTable, confere as
colunas obrigatórias e coage os tipos; qualquer checagem `fatal` devolve None no lugar do
DataFrame, e a importação aborta antes de gravar qualquer coisa. As mensagens carregam coluna e
local agregados, NUNCA bytes do código do aluno.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from api.classroom_import.domain.value_objects.import_report import ImportCheck
from api.classroom_import.infrastructure.implementations.progsnap_zip_extractor import (
    find_code_snapshots_file,
)

# Obrigatórias DESTA ferramenta, além das mandatórias do padrão ProgSnap2:
# sem elas o pipeline de mastery não tem como rotular first-attempts nem agrupar por aluno/KC.
_REQUIRED_COLUMNS = (
    "SubjectID",
    "AssignmentID",
    "ProblemID",
    "CodeStateID",
    "EventType",
    "Score",
    "ServerTimestamp",
)


def read_main_table(main_path: Path) -> tuple[pd.DataFrame | None, list[ImportCheck]]:
    checks: list[ImportCheck] = []

    try:
        # utf-8-sig consome o BOM transparente: BOM vira warning no clean, não
        # falha aqui. Detecção heurística de encoding seria dependência + ambiguidade num v1.
        df = pd.read_csv(main_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        # Não interpolar o detalhe do erro: pode carregar bytes do código do aluno.
        checks.append(
            ImportCheck(
                check="encoding",
                severity="fatal",
                message="arquivo não pôde ser decodificado como UTF-8.",
                location=Path(main_path).name,
            )
        )
        return None, checks

    missing = [col for col in _REQUIRED_COLUMNS if col not in df.columns]
    for col in missing:
        checks.append(
            ImportCheck(
                check="missing_required_column",
                severity="fatal",
                message=f"coluna obrigatória ausente: {col}.",
                location=f"{Path(main_path).name}:{col}",
            )
        )

    if any(c.severity == "fatal" for c in checks):
        # Qualquer falha dura: nada a devolver; a importação aborta sem gravar.
        return None, checks

    # Coerção de tipos espelhando data_loader.load_main_table:17-27 — não confia nos tipos do
    # CSV; errors="coerce" transforma lixo em NaT/NA em vez de explodir (a contagem de coerções
    # falhas vira anomalia graduada no clean/viability, não aqui).
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True, errors="coerce")
    df["AssignmentID"] = pd.to_numeric(df["AssignmentID"], errors="coerce").astype("Int64")
    df["ProblemID"] = pd.to_numeric(df["ProblemID"], errors="coerce").astype("Int64")

    # Score CONTÍNUO mas tipado: num ProgSnap2 real ele chega como string
    # ("1.0"), vazio ou "N/A". Sem esta coerção a coluna fica object, `Score == 1.0` (clean.py)
    # é False p/ toda linha — a binarização zera em silêncio e a turma inteira vira EDA-only —,
    # e `float(row.Score)` estoura no persist. data_loader.load_main_table NÃO coage Score
    # (CSEDM é bem-comportado); aqui é a fronteira que paga a tolerância do dado real.
    n_before_nan = int(df["Score"].isna().sum())
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
    n_coerce_failed = int(df["Score"].isna().sum()) - n_before_nan
    if n_coerce_failed > 0:
        # Graduado, não fatal: NaN vira null no persist (pd.isna) e fica fora da binarização.
        checks.append(
            ImportCheck(
                check="score_coercion",
                severity="warning",
                message=f"{n_coerce_failed} valor(es) de Score não numérico(s) coagido(s) a vazio.",
                count=n_coerce_failed,
            )
        )

    return df, checks


def read_code_snapshots(raw_dir: Path) -> dict[str, str]:
    """{CodeStateID: código Java}, para juntar o snapshot a cada evento na limpeza.

    Sem CodeStates no upload, um dict vazio: a limpeza trata todo evento como órfão (aviso), nunca
    explode.
    """
    path = find_code_snapshots_file(Path(raw_dir))
    if path is None:
        return {}
    table = pd.read_csv(path, encoding="utf-8-sig")
    return dict(zip(table["CodeStateID"].astype(str), table["Code"].fillna("")))


class ProgSnapCsvReader:
    """IProgSnapTableReader sobre os CSVs do upload."""

    def read_main_table(self, path: Path) -> tuple[pd.DataFrame | None, list[ImportCheck]]:
        return read_main_table(path)

    def read_code_snapshots(self, raw_dir: Path) -> dict[str, str]:
        return read_code_snapshots(raw_dir)
