# Contagens por problema, por conceito e por aluno, direto do dado limpo, sem tocar em modelo.

from __future__ import annotations

import pandas as pd

from api.classroom_import.domain.services.submission_event import COMPILE_ERROR, RUN_PROGRAM
from api.mastery_dashboard.domain.value_objects.submission_statistics import (
    KnowledgeComponentStatistics,
    ProblemStatistics,
    StudentActivity,
)


def _program_runs(cleaned: pd.DataFrame) -> pd.DataFrame:
    # Só Run.Program, em ordem cronológica estável, com o aluno como texto (o SQLite devolve int).
    runs = cleaned[cleaned["event_type"] == RUN_PROGRAM]
    return runs.assign(student_id=runs["student_id"].astype(str)).sort_values(
        "submitted_at", kind="stable"
    )


def _compile_errors(cleaned: pd.DataFrame) -> pd.DataFrame:
    errors = cleaned[cleaned["event_type"] == COMPILE_ERROR]
    return errors.assign(student_id=errors["student_id"].astype(str))


def compute_problem_statistics(cleaned: pd.DataFrame) -> list[ProblemStatistics]:
    # Do problema em que a turma mais erra ao que mais acerta.
    runs = _program_runs(cleaned)
    if runs.empty:
        return []
    by_problem = runs.groupby("problem_id")
    run_counts = by_problem.size()
    success_rate = by_problem["is_correct"].mean()
    students_attempted = by_problem["student_id"].nunique()
    correct = runs[runs["is_correct"] == 1]
    students_completed = correct.groupby("problem_id")["student_id"].nunique()

    # A n-ésima execução do aluno no problema; completar é a primeira correta.
    attempt_number = runs.groupby(["student_id", "problem_id"]).cumcount() + 1
    first_correct = (
        runs.assign(attempt_number=attempt_number)
        .loc[runs["is_correct"] == 1]
        .groupby(["student_id", "problem_id"])["attempt_number"]
        .min()
    )
    median_attempts = first_correct.groupby(level="problem_id").median()
    error_counts = _compile_errors(cleaned).groupby("problem_id").size()

    rows = [
        ProblemStatistics(
            problem_id=int(problem_id),
            success_rate=float(success_rate[problem_id]),
            median_attempts_to_complete=(
                float(median_attempts[problem_id]) if problem_id in median_attempts.index else None
            ),
            students_attempted=int(students_attempted[problem_id]),
            students_completed=int(students_completed.get(problem_id, 0)),
            compile_errors_per_run=float(error_counts.get(problem_id, 0) / run_counts[problem_id]),
        )
        for problem_id in run_counts.index
    ]
    return sorted(rows, key=lambda row: (row.success_rate, row.problem_id))


def compute_knowledge_component_statistics(
    cleaned: pd.DataFrame, kcs_by_problem: dict[int, list[int]]
) -> list[KnowledgeComponentStatistics]:
    # A taxa de acerto do conceito soma as execuções de todos os problemas que o exigem.
    runs = _program_runs(cleaned)
    problems_by_kc: dict[int, list[int]] = {}
    for problem_id, kc_ids in kcs_by_problem.items():
        for kc_id in kc_ids:
            problems_by_kc.setdefault(kc_id, []).append(problem_id)

    rows = []
    for kc_id, problem_ids in problems_by_kc.items():
        kc_runs = runs[runs["problem_id"].isin(problem_ids)]
        if kc_runs.empty:
            continue
        rows.append(
            KnowledgeComponentStatistics(
                kc_id=kc_id, success_rate=float(kc_runs["is_correct"].mean()), runs=int(len(kc_runs))
            )
        )
    return sorted(rows, key=lambda row: (row.success_rate, row.kc_id))


def compute_student_activity(cleaned: pd.DataFrame) -> dict[str, StudentActivity]:
    # Por aluno, quantos problemas tentou e completou, quantas execuções e erros de compilação.
    runs = _program_runs(cleaned)
    if runs.empty:
        return {}
    by_student = runs.groupby("student_id")
    run_counts = by_student.size()
    attempted = by_student["problem_id"].nunique()
    completed = runs[runs["is_correct"] == 1].groupby("student_id")["problem_id"].nunique()
    error_counts = _compile_errors(cleaned).groupby("student_id").size()
    return {
        str(student_id): StudentActivity(
            student_id=str(student_id),
            completed=int(completed.get(student_id, 0)),
            attempted=int(attempted[student_id]),
            runs=int(run_counts[student_id]),
            compile_errors=int(error_counts.get(student_id, 0)),
        )
        for student_id in run_counts.index
    }
