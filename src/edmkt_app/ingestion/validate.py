"""Estágio B da ingestão — pré-voo de falhas duras (INGEST-01 / D-05 nível 1 / D-06).

Primeira linha de defesa contra "ProgSnap2 tratado como CSEDM-shaped" (Pitfall 1): o CSEDM é
bem-comportado, um upload real não. Função pura — recebe um caminho, lê e coage tipos sem
confiar no CSV, devolve (DataFrame | None, list[ReportItem]); NÃO persiste nada (D-06) e não
importa o núcleo nem a persistência. Qualquer item `severity="fatal"` ⇒ DataFrame None, e o
service aborta antes de qualquer escrita.

Mensagens carregam coluna/local agregado, NUNCA bytes de código de aluno (Information
Disclosure, T-03-06).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from edmkt_app.ingestion.report import ReportItem

# Obrigatórias DESTA ferramenta (RESEARCH §Anomalias) — além das mandatórias da spec ProgSnap2:
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


def validate(main_path: Path) -> tuple[pd.DataFrame | None, list[ReportItem]]:
    items: list[ReportItem] = []

    try:
        # utf-8-sig consome o BOM transparente (Discretion): BOM vira warning no clean, não
        # falha aqui. Detecção heurística de encoding seria dependência + ambiguidade num v1.
        df = pd.read_csv(main_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        # Não interpolar o detalhe do erro: pode carregar bytes do código do aluno (T-03-06).
        items.append(
            ReportItem(
                check="encoding",
                severity="fatal",
                message="arquivo não pôde ser decodificado como UTF-8.",
                location=Path(main_path).name,
            )
        )
        return None, items

    missing = [col for col in _REQUIRED_COLUMNS if col not in df.columns]
    for col in missing:
        items.append(
            ReportItem(
                check="missing_required_column",
                severity="fatal",
                message=f"coluna obrigatória ausente: {col}.",
                location=f"{Path(main_path).name}:{col}",
            )
        )

    if any(i.severity == "fatal" for i in items):
        # D-06: qualquer falha dura ⇒ nada a devolver; o service aborta sem persistir.
        return None, items

    # Coerção de tipos espelhando data_loader.load_main_table:17-27 — não confia nos tipos do
    # CSV; errors="coerce" transforma lixo em NaT/NA em vez de explodir (a contagem de coerções
    # falhas vira anomalia graduada no clean/viability, não aqui).
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True, errors="coerce")
    df["AssignmentID"] = pd.to_numeric(df["AssignmentID"], errors="coerce").astype("Int64")
    df["ProblemID"] = pd.to_numeric(df["ProblemID"], errors="coerce").astype("Int64")

    return df, items
