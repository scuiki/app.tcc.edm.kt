"""Fonte única do quadro de modelagem — a forma estrutural do fix de training-serving skew.

O bug original: `train.py` e `mastery_service.py` liam o Parquet canônico cada um por si e
nenhum recortava `Run.Program`, então o modelo treinava sobre 57,6% de eventos rotulados como
erro cujo Java não compila. A primeira correção (chamar `utils.run_program_only` nos dois) deixa
a garantia dependendo de dois chamadores LEMBRAREM de chamar — e um terceiro consumidor futuro
reintroduz o bug.

Aqui a garantia deixa de depender de memória: quem faz modelagem recebe o quadro pronto e não
tem acesso ao Parquet cru. A EDA continua lendo o canônico por conta própria, de propósito —
ela PRECISA dos Compile.Error para a taxa de erro de compilação.
"""

from __future__ import annotations

import inspect

import pandas as pd
import pytest

from edmkt_app import modeling_frame, settings
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos


def _seed(conn, data_root) -> int:
    created = "2019-03-01T00:00:00+00:00"
    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name="Turma X", created_at=created)
    )
    assignment_id = repos.AssignmentRepository(conn).insert(
        models.Assignment(
            id=None,
            turma_id=turma_id,
            name="Assignment 439",
            progsnap_assignment_id=439,
            current_version_id=None,
            created_at=created,
            status="ready_for_kc_generation",
        )
    )
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for i, (event, code) in enumerate(
        [
            ("Run.Program", "public int f(int x) { return x + 1; }"),
            ("Compile.Error", "public int oops( { return ;;; }"),
            ("Run.Program", "public int g(int a) { return a; }"),
            ("Compile.Error", "public int bad( {"),
        ]
    ):
        rows.append(
            {
                "student_id": "S1",
                "progsnap_assignment_id": 439,
                "problem_id": 1,
                "code_snapshot_id": f"c{i}",
                "code": code,
                "score": 0.0,
                "submitted_at": base + pd.Timedelta(minutes=i),
                "event_type": event,
                "is_correct": 0,
            }
        )
    df = pd.DataFrame(rows)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")
    clean_dir = data_root / "turma-x" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(clean_dir / "assignment_439.parquet", engine="pyarrow", index=False)
    return assignment_id


def test_frame_carries_only_run_program(tmp_db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    assignment_id = _seed(tmp_db, tmp_path)

    frame = modeling_frame.load_modeling_frame(tmp_db, assignment_id)

    assert set(frame.events["event_type"].unique()) == {"Run.Program"}
    assert len(frame.events) == 2


def test_frame_carries_the_identifiers_the_callers_need(tmp_db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    assignment_id = _seed(tmp_db, tmp_path)

    frame = modeling_frame.load_modeling_frame(tmp_db, assignment_id)

    assert str(frame.turma_slug) == "turma-x"
    assert frame.assignment_id.value == 439


def test_missing_assignment_raises(tmp_db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    with pytest.raises(ValueError, match="assignment"):
        modeling_frame.load_modeling_frame(tmp_db, 999)


def test_orphan_turma_raises_instead_of_attributeerror(tmp_db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    # WR-01 já pego uma vez em api/dashboard: turma ausente virava AttributeError em turma.name
    # e subia como 500 cru. A resolução de nomes agora é de um lugar só — a guarda mora com ela.
    #
    # A FK do SQLite é POR-CONEXÃO: connect() liga foreign_keys, mas outra conexão (ou uma
    # cirurgia manual no app.db) pode apagar a turma sob o assignment. É esse estado que se
    # reproduz aqui desligando o PRAGMA — não um INSERT inválido, que a FK barraria.
    assignment_id = _seed(tmp_db, tmp_path)
    tmp_db.execute("PRAGMA foreign_keys=OFF;")
    tmp_db.execute("DELETE FROM classroom;")
    tmp_db.execute("PRAGMA foreign_keys=ON;")

    with pytest.raises(ValueError, match="turma"):
        modeling_frame.load_modeling_frame(tmp_db, assignment_id)


@pytest.mark.parametrize("module_name", ["edmkt_app.train", "edmkt_app.mastery_service"])
def test_modeling_modules_cannot_reach_the_raw_parquet(module_name):
    # A garantia estrutural: sem caminho até o Parquet cru, não há o que esquecer de filtrar.
    import importlib

    source = inspect.getsource(importlib.import_module(module_name))
    assert "read_parquet" not in source


def test_eda_still_reads_the_full_canonical_stream():
    # Contraprova: a EDA NÃO deve passar pelo quadro de modelagem — a taxa de erro de compilação
    # depende justamente dos eventos que o recorte remove.
    from edmkt_app import eda

    source = inspect.getsource(eda)
    assert "read_parquet" in source
    assert "load_modeling_frame" not in source
