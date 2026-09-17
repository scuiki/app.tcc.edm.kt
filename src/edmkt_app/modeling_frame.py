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

`data_root` vem por parâmetro em vez de global: os dois chamadores já têm o seu (e os testes o
monkeypatcham), e um segundo global aqui seria mais um lugar para divergir.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from edmkt_app import utils
from edmkt_app.persistence import repositories as repos
from edmkt_app.values import ProgSnapAssignmentId, TurmaSlug


@dataclass(frozen=True)
class ModelingFrame:
    """Eventos prontos para modelar + os identificadores que os chamadores derivavam sozinhos."""

    events: pd.DataFrame
    turma_slug: TurmaSlug
    assignment_id: ProgSnapAssignmentId
    turma_id: int  # id do banco — o artefato é persistido por (turma, assignment)


def canonical_parquet_path(
    data_root: Path, turma_slug: TurmaSlug, assignment_id: ProgSnapAssignmentId
) -> Path:
    return data_root / turma_slug / "clean" / f"assignment_{assignment_id}.parquet"


def load_modeling_frame(
    conn: sqlite3.Connection, assignment_id: int, *, data_root: Path
) -> ModelingFrame:
    """Resolve nomes → caminho → Parquet → recorte, e devolve o quadro já modelável.

    `assignment_id` é o id do BANCO; o do ProgSnap2 sai do nome e volta no frame (999.2).
    """
    assignment = repos.AssignmentRepository(conn).get(assignment_id)
    if assignment is None:
        raise ValueError(f"assignment {assignment_id} inexistente")
    turma = repos.TurmaRepository(conn).get(assignment.turma_id)
    if turma is None:
        # Turma órfã (FK não-cascade por-conexão): erro nomeado em vez de AttributeError em
        # turma.name, que já subiu como 500 cru uma vez (WR-01 em api/dashboard).
        raise ValueError(f"turma {assignment.turma_id} inexistente")

    turma_slug = TurmaSlug.from_name(turma.name)
    progsnap_aid = ProgSnapAssignmentId.from_name(assignment.name)
    pq = canonical_parquet_path(Path(data_root), turma_slug, progsnap_aid)

    return ModelingFrame(
        events=utils.run_program_only(pd.read_parquet(pq, engine="pyarrow")),
        turma_slug=turma_slug,
        assignment_id=progsnap_aid,
        turma_id=assignment.turma_id,
    )
