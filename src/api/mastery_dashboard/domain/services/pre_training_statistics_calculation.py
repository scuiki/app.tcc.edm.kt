"""Calcula as PreTrainingStatistics: as estatísticas das submissões que existem ANTES de qualquer
treino.

O professor tem estas estatísticas desde a importação: são calculadas direto do dado limpo e nunca
tocam um modelo. Funções puras (DataFrame entra, dicionário sai); ler o Parquet é do use case.
"""

from __future__ import annotations

import pandas as pd

from api.classroom_import.domain.services.submission_event import COMPILE_ERROR, RUN_PROGRAM

from api.mastery_dashboard.domain.value_objects.pre_training_statistics import PreTrainingStatistics


def compute_pre_training_statistics(cleaned_submissions: pd.DataFrame) -> PreTrainingStatistics:
    return PreTrainingStatistics(
        success_rate=success_rate_by_assignment(cleaned_submissions),
        learning_curve=learning_curve(cleaned_submissions),
        compile_error_rate=compile_error_rate_by_assignment(cleaned_submissions),
    )


def success_rate_by_assignment(cleaned: pd.DataFrame) -> dict[int, float]:
    """A média de `is_correct` sobre os eventos Run.Program, por assignment."""
    runs = cleaned[cleaned["event_type"] == RUN_PROGRAM]
    rates = runs.groupby("progsnap_assignment_id")["is_correct"].mean()
    return {int(aid): float(rate) for aid, rate in rates.items()}


def learning_curve(cleaned: pd.DataFrame) -> dict[int, float]:
    """A média de `is_correct` pelo número da tentativa (a n-ésima Run.Program de cada aluno)."""
    runs = cleaned[cleaned["event_type"] == RUN_PROGRAM].sort_values("submitted_at")
    attempt = runs.groupby(["student_id", "progsnap_assignment_id"]).cumcount()
    curve = runs.assign(attempt_num=attempt).groupby("attempt_num")["is_correct"].mean()
    return {int(k): float(v) for k, v in curve.sort_index().items()}


def compile_error_rate_by_assignment(cleaned: pd.DataFrame) -> dict[int, float]:
    """Erros de compilação POR tentativa de execução (CE / Run), por assignment.

    Não é CE / (CE + Run): a média sobre todos os eventos misturava os dois tipos e variava com
    quantas execuções o aluno teve, o que tornava a métrica incomparável com a convenção.
    """
    runs = cleaned[cleaned["event_type"] == RUN_PROGRAM]
    compile_errors = cleaned[cleaned["event_type"] == COMPILE_ERROR]
    run_counts = runs.groupby("progsnap_assignment_id").size()
    error_counts = (
        compile_errors.groupby("progsnap_assignment_id").size()
        .reindex(run_counts.index, fill_value=0)
    )
    rate = (error_counts / run_counts).fillna(0.0)
    return {int(aid): float(v) for aid, v in rate.items()}
