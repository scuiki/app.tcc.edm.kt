"""Contrato de saída estruturado da ingestão por severidade (D-07).

Dataclasses puras (sem I/O, sem SQL), espelhando persistence/models.py: a API devolve este
objeto e a SPA decide a renderização (banner/cards/cor) — o backend NÃO emite HTML. Testável
por severidade, não por strings de UI. `message` já vem redigido em pt-BR (Claude's Discretion
D-07). NUNCA carregar o `Code` cru do aluno em nenhum campo (Information Disclosure — só
contagens/locais agregados).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

# fatal => rejeita, nada persiste (D-05 nível 1); warning => anomalia auto-tratada (nível 2);
# viability => persiste mas marca EDA-only / avisa piso (nível 3, D-09).
Severity = Literal["fatal", "warning", "viability"]


@dataclass(frozen=True)
class ReportItem:
    # frozen = write-once (espelha ModelArtifact): um item de relatório nunca é mutado depois
    # de emitido pelo estágio que o produziu (validate/clean/viability).
    check: str
    severity: Severity
    message: str
    count: Optional[int] = None
    location: Optional[str] = None


@dataclass
class AssignmentSummary:
    assignment_id: int
    n_students_eligible: int
    n_problems: int
    n_submissions: int
    both_classes_present: bool
    trainable: bool  # False => EDA-only (D-05/D-08): persiste, mas não pode treinar
    reasons: list[str] = field(default_factory=list)


@dataclass
class IngestReport:
    items: list[ReportItem]
    dataset_summary: dict  # alunos/assignments/problemas/submissões (INGEST-02)
    per_assignment: list[AssignmentSummary]

    @property
    def has_fatal(self) -> bool:
        # has_fatal governa o D-06: True => abortar antes de qualquer escrita.
        return any(i.severity == "fatal" for i in self.items)
