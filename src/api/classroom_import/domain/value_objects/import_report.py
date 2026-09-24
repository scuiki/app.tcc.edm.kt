# NUNCA carregar código Java do aluno neste objeto; só contagens e locais agregados.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# fatal recusa e não grava nada; warning é anomalia tratada; viability grava mas avisa.
Severity = Literal["fatal", "warning", "viability"]


@dataclass(frozen=True)
class ImportCheck:
    # Uma checagem emitida nunca é alterada por quem vem depois (frozen).
    check: str
    severity: Severity
    message: str
    count: int | None = None
    location: str | None = None


@dataclass
class AssignmentTrainability:
    progsnap_assignment_id: int
    n_students_eligible: int
    n_problems: int
    n_submissions: int
    both_classes_present: bool
    trainable: bool  # False, statistics_only, grava mas não pode treinar
    reasons: list[str] = field(default_factory=list)


@dataclass
class ClassroomImportReport:
    checks: list[ImportCheck]
    dataset_summary: dict  # alunos / assignments / problemas / submissões
    per_assignment: list[AssignmentTrainability]

    @property
    def has_fatal(self) -> bool:
        return any(c.severity == "fatal" for c in self.checks)

    @classmethod
    def nothing_imported(cls, checks: list[ImportCheck]) -> "ClassroomImportReport":
        # O relatório de quando nada foi gravado (fatal no pré-voo ou outro job rodando).
        return cls(
            checks=checks,
            dataset_summary={"n_students": 0, "n_assignments": 0, "n_problems": 0, "n_submissions": 0},
            per_assignment=[],
        )
