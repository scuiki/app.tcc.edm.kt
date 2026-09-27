# O que aconteceu nas execuções, contado do dado limpo e sem nenhum modelo.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProblemStatistics:
    problem_id: int
    success_rate: float  # execuções corretas sobre execuções, todos os alunos juntos
    median_attempts_to_complete: float | None  # None quando ninguém completou
    students_attempted: int
    students_completed: int  # ao menos uma execução correta no problema
    compile_errors_per_run: float  # CE sobre Run, pode passar de 1


@dataclass(frozen=True)
class KnowledgeComponentStatistics:
    kc_id: int
    success_rate: float  # sobre as execuções de todos os problemas que exigem o conceito
    runs: int


@dataclass(frozen=True)
class StudentActivity:
    student_id: str
    completed: int  # problemas com ao menos uma execução correta
    attempted: int  # problemas com ao menos uma execução
    runs: int
    compile_errors: int
