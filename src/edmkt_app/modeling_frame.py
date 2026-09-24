"""Fonte única do quadro de dados que treino e inferência consomem.

O Parquet canônico da Fase 3 guarda `{Run.Program, Compile.Error}` de propósito: o filtro de
EventType é o dedup do par de mesmo timestamp (clean.py D-10) e a EDA precisa dos compile errors.
Modelagem é outra história — o TCC 1 treinou o Code-DKT só sobre `Run.Program`, e é esse o dado
que o teste de regressão usa como oráculo.

Este módulo existe para que essa diferença tenha UM lugar. Antes dele, `train.py` e
`mastery_service.py` montavam o caminho e liam o Parquet cada um por si; ambos esqueceram o
recorte, o modelo treinou sobre 57,6% de eventos rotulados como erro e o first-attempt AUC caiu
para 0,6959, fora da banda ±3pp. Uma função compartilhada resolveria o caso de hoje; a fonte
única resolve o caso de amanhã, porque quem faz modelagem passa a receber o quadro pronto.

O caminho do Parquet sai de `data_layout`, o único lugar que conhece a árvore de `data/`.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
import pandas as pd

from api.shared.infrastructure import data_layout
from api.classroom_import.domain import submission_event
from api.assignments.domain.progsnap_assignment_id import ProgSnapAssignmentId
from api.assignments.domain.classroom_slug import ClassroomSlug
from api.assignments.infrastructure.sqlite_classroom_repository import SqliteClassroomRepository
from api.assignments.infrastructure.sqlite_assignment_repository import SqliteAssignmentRepository


@dataclass(frozen=True)
class ModelingFrame:
    """Eventos prontos para modelar + os identificadores que os chamadores derivavam sozinhos."""

    events: pd.DataFrame
    turma_slug: ClassroomSlug
    assignment_id: ProgSnapAssignmentId
    classroom_id: int  # id do banco — o artefato é persistido por (turma, assignment)


def load_modeling_frame(conn: sqlite3.Connection, assignment_id: int) -> ModelingFrame:
    """Resolve nomes → caminho → Parquet → recorte, e devolve o quadro já modelável.

    `assignment_id` é o id do BANCO; o do ProgSnap2 vem da coluna própria e volta no frame (999.2).
    """
    assignment = SqliteAssignmentRepository(conn).get(assignment_id)
    if assignment is None:
        raise ValueError(f"assignment {assignment_id} inexistente")
    turma = SqliteClassroomRepository(conn).get(assignment.classroom_id)
    if turma is None:
        # Turma órfã (FK não-cascade por-conexão): erro nomeado em vez de AttributeError em
        # turma.name, que já subiu como 500 cru uma vez (WR-01 em api/dashboard).
        raise ValueError(f"turma {assignment.classroom_id} inexistente")

    turma_slug = ClassroomSlug.from_name(turma.name)
    progsnap_aid = ProgSnapAssignmentId(assignment.progsnap_assignment_id)
    pq = data_layout.cleaned_submissions_path(turma_slug, progsnap_aid)

    return ModelingFrame(
        events=submission_event.keep_only_program_runs(pd.read_parquet(pq, engine="pyarrow")),
        turma_slug=turma_slug,
        assignment_id=progsnap_aid,
        classroom_id=assignment.classroom_id,
    )
