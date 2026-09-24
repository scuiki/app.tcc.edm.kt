"""EDA de turma a partir do Parquet canônico (DASH-04, D-06) — SEM modelo treinado.

A EDA é a view SEMPRE disponível: lê só o Parquet canônico da Fase 3 (CANONICAL_COLUMNS
de clean.py) e nunca toca um artefato de modelo nem a stack de inferência (D-06). O professor
tem dashboard de EDA antes mesmo do treino.

Módulo majoritariamente puro (DataFrame-in → out), no estilo de `ingestion/clean.py:9`. O
ÚNICO I/O é o `pd.read_parquet` num wrapper fino (`_read_canonical`), reaproveitado pelas
funções públicas que recebem o caminho do Parquet.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from edmkt_app import settings
from edmkt_app.values import ProgSnapAssignmentId, TurmaSlug

# EDA NÃO importa train.py/persistence: aquele lado puxa torch + ArtifactStore e quebraria a
# invariante "EDA roda sem modelo" (D-06). _slug/_progsnap_aid são triviais e reproduzidos aqui.
# IN-02: o stream canônico (clean.py ALLOWED_EVENTS) contém exatamente {Run.Program, Compile.Error};
# esses dois tipos são os únicos consumidos abaixo (RUN_EVENT/COMPILE_ERROR_EVENT) — sem precisar
# importar ALLOWED_EVENTS só para documentar, o que acoplava a EDA a ingestion.clean no import.
RUN_EVENT = "Run.Program"
COMPILE_ERROR_EVENT = "Compile.Error"


def _read_canonical(pq: Path | str) -> pd.DataFrame:
    # Único ponto de I/O do módulo (T-06-05): o caminho vem de IDs int + _slug/_progsnap_aid
    # internos, NUNCA de caminho de cliente; o read não carrega artefato de modelo (D-06).
    return pd.read_parquet(pq, engine="pyarrow")


def canonical_parquet_path(turma_name: str, assignment_name: str) -> Path:
    """Deriva o caminho do Parquet canônico igual a `train.py:89` — a partir de nomes internos."""
    return (
        settings.DATA_ROOT
        / TurmaSlug.from_name(turma_name)
        / "clean"
        / f"assignment_{ProgSnapAssignmentId.from_name(assignment_name)}.parquet"
    )


# --- Agregações puras (DataFrame-in → out) ---------------------------------------


def _success_rate_by_assignment(df: pd.DataFrame) -> dict[int, float]:
    runs = df[df["EventType"] == RUN_EVENT]
    return {int(aid): float(rate) for aid, rate in runs.groupby("AssignmentID")["correct"].mean().items()}


def _learning_curve(df: pd.DataFrame) -> dict[int, float]:
    runs = df[df["EventType"] == RUN_EVENT].sort_values("ServerTimestamp")
    # attempt_num = cumcount por (aluno, assignment): a n-ésima tentativa de Run.Program do aluno.
    attempt = runs.groupby(["SubjectID", "AssignmentID"]).cumcount()
    curve = runs.assign(attempt_num=attempt).groupby("attempt_num")["correct"].mean()
    return {int(k): float(v) for k, v in curve.sort_index().items()}


def _compile_error_rate_by_assignment(df: pd.DataFrame) -> dict[int, float]:
    # WR-03: a taxa é CE_count / Run_count (compile-errors POR tentativa de execução), não
    # CE_count / (CE+Run). A média sobre TODOS os eventos misturava os dois tipos e variava
    # com quantos Run.Program o aluno teve, tornando a métrica incomparável com a convenção.
    runs = df[df["EventType"] == RUN_EVENT]
    ce = df[df["EventType"] == COMPILE_ERROR_EVENT]
    run_counts = runs.groupby("AssignmentID").size()
    ce_counts = ce.groupby("AssignmentID").size().reindex(run_counts.index, fill_value=0)
    rate = (ce_counts / run_counts).fillna(0.0)
    return {int(aid): float(v) for aid, v in rate.items()}


# --- API pública: caminho-in → agregado-out (single read no wrapper) -------------


def success_rate_by_assignment(pq: Path | str) -> dict[int, float]:
    """Taxa de acerto por AssignmentID = média de `correct` sobre eventos Run.Program."""
    return _success_rate_by_assignment(_read_canonical(pq))


def learning_curve(pq: Path | str) -> dict[int, float]:
    """Curva de aprendizado: média de `correct` por número de tentativa (cumcount), ordenada."""
    return _learning_curve(_read_canonical(pq))


def compile_error_rate_by_assignment(pq: Path | str) -> dict[int, float]:
    """Taxa de compile-error por AssignmentID = Compile.Error por tentativa (CE_count/Run_count)."""
    return _compile_error_rate_by_assignment(_read_canonical(pq))
