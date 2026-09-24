"""ImportClassroomDatasetUseCase com a infraestrutura real (fixture `import_classroom`).

Cobre o que as etapas puras não exercitam: a gravação atômica (uma falha no meio não deixa resto),
o dado limpo gravado no banco, a preservação do cru e a trava de job (ocupada não grava; liberada mesmo
sob exceção). Herméticos, sobre `tmp_db` + tmp_path; nunca o CSEDM real.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from api.classroom_import.domain.services.submission_cleaning import CLEANED_COLUMNS

# MainTable com DUAS classes nos first-attempts (≥1 acerto E ≥1 erro) ⇒ assignment trainable
#. CodeStateID casa 1:1 com o CodeStates.csv abaixo (sem órfãos neste fixture base).
_MAIN_TABLE = (
    "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp\n"
    "S1,439,1,c1,Run.Program,0.0,2019-03-01T08:00:00Z\n"
    "S1,439,2,c2,Run.Program,1.0,2019-03-01T08:01:00Z\n"
    "S2,439,1,c3,Run.Program,1.0,2019-03-01T08:02:00Z\n"
    "S2,439,2,c4,Run.Program,0.5,2019-03-01T08:03:00Z\n"
)

# CodeStates: o snapshot Java por CodeStateID, gravado junto com a tentativa. Score 0.5 acima
# fica preservado contínuo.
_CODE_STATES = (
    "CodeStateID,Code\n"
    'c1,"public int f(){return 0;}"\n'
    'c2,"public int g(){return 1;}"\n'
    'c3,"public int h(){return 1;}"\n'
    'c4,"public int k(){return 2;}"\n'
)


def _make_raw(root: Path, main_table: str = _MAIN_TABLE) -> tuple[Path, Path]:
    """Monta data/<slug>/raw/ com MainTable.csv + CodeStates/CodeStates.csv. Devolve (raw, main)."""
    raw = root / "turma-x" / "raw"
    (raw / "CodeStates").mkdir(parents=True)
    main = raw / "MainTable.csv"
    main.write_text(main_table, encoding="utf-8")
    (raw / "CodeStates" / "CodeStates.csv").write_text(_CODE_STATES, encoding="utf-8")
    return raw, main



def _counts(conn) -> tuple[int, int, int]:
    t = conn.execute("SELECT COUNT(*) AS n FROM classroom;").fetchone()["n"]
    a = conn.execute("SELECT COUNT(*) AS n FROM assignment;").fetchone()["n"]
    s = conn.execute("SELECT COUNT(*) AS n FROM submission;").fetchone()["n"]
    return t, a, s


class _FailsAfterWriting:
    """Grava as submissões e só então falha: o meio da transação, com linhas já escritas."""

    def __init__(self, real) -> None:
        self._real = real

    def add_many(self, assignment_id, events) -> None:
        self._real.add_many(assignment_id, events)
        raise RuntimeError("disk full depois dos INSERTs (simulado)")


def _holder_pid(conn):
    return conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()["holder_pid"]


# --- caminho feliz: grava turma + assignments + submissões ------------------------------


def test_happy_persists_classroom_assignment_and_submissions(import_classroom, tmp_db, data_root):
    conn = tmp_db
    raw, main = _make_raw(data_root)

    report = import_classroom(raw, "Turma X", main)

    assert not report.has_fatal
    n_turmas, n_assign, n_sub = _counts(conn)
    assert n_turmas == 1
    assert n_assign == 1  # um único AssignmentID (439) no fixture
    assert n_sub == 4  # 4 eventos Run.Program, todos com snapshot (sem órfão)

    # Assignment ganhou status do gate: ambas as classes presentes ⇒ trainable.
    status = conn.execute("SELECT status FROM assignment;").fetchone()["status"]
    assert status == "ready_for_kc_generation"


def test_the_cleaned_data_is_readable_by_assignment(import_classroom, sqlite_submissions, tmp_db, data_root):
    conn = tmp_db
    raw, main = _make_raw(data_root)
    import_classroom(raw, "Turma X", main)

    assignment_id = conn.execute("SELECT id FROM assignment;").fetchone()["id"]
    back = sqlite_submissions.list_by_assignment(assignment_id)

    # As 9 colunas que o ml/ consome, na ordem.
    assert list(back.columns) == CLEANED_COLUMNS
    # Score contínuo preservado: o 0.5 não foi destruído na binarização.
    assert 0.5 in set(back["score"].tolist())
    # O código Java vai junto (é o snapshot do treino e das estatísticas).
    assert back["code"].notna().all()


def test_raw_csv_preserved_after_ingest(import_classroom, tmp_db, data_root):
    # o cru continua em raw/ pós-ingest (reprodutibilidade / re-ingest).
    conn = tmp_db
    raw, main = _make_raw(data_root)
    import_classroom(raw, "Turma X", main)
    assert main.exists()
    assert (raw / "CodeStates" / "CodeStates.csv").exists()


# --- commit atômico (falha no meio não deixa resto) ----------------------------------


def test_atomicity_failure_mid_persist_leaves_nothing(import_classroom, sqlite_submissions, tmp_db, data_root):
    # Falha dura DEPOIS dos INSERTs das submissões: o ROLLBACK desfaz tudo, turma inclusive.
    conn = tmp_db
    raw, main = _make_raw(data_root)

    with pytest.raises(RuntimeError):
        import_classroom(raw, "Turma X", main, submissions=_FailsAfterWriting(sqlite_submissions))

    # SQLite inalterado: 0 turmas/assignments/submissions (ROLLBACK).
    assert _counts(conn) == (0, 0, 0)
    # Release garantido mesmo sob exceção: a trava voltou a NULL.
    assert _holder_pid(conn) is None


def test_fatal_preflight_persists_nothing(import_classroom, tmp_db, data_root):
    # Coluna obrigatória ausente ⇒ has_fatal True e NADA persiste.
    conn = tmp_db
    bad_main = (
        "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,ServerTimestamp\n"  # sem Score
        "S1,439,1,c1,Run.Program,2019-03-01T08:00:00Z\n"
    )
    raw, main = _make_raw(data_root, main_table=bad_main)

    report = import_classroom(raw, "Turma X", main)

    assert report.has_fatal
    assert _counts(conn) == (0, 0, 0)


# --- Lock Timing: busy não persiste; release garantido --------------------------------------


def test_lock_busy_does_not_persist(import_classroom, tmp_db, data_root):
    # Trava ocupada por um PID VIVO (o próprio processo de teste) ⇒ ingest devolve "busy" e
    # NADA persiste (turma count inalterado). Não removemos a trava de outro dono.
    conn = tmp_db
    raw, main = _make_raw(data_root)
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='ingestion', "
        "acquired_at='2026-06-21T00:00:00Z' WHERE id=1;",
        (os.getpid(),),
    )

    report = import_classroom(raw, "Turma X", main)

    assert report.has_fatal  # relatório "busy" carrega um item fatal
    assert any(c.check == "another_job_running" for c in report.checks)
    assert _counts(conn) == (0, 0, 0)
    # A trava do dono vivo NÃO foi tocada por nós.
    assert _holder_pid(conn) == os.getpid()


def test_lock_released_after_successful_ingest(import_classroom, tmp_db, data_root):
    # Após um ingest bem-sucedido, o `with lock` libera a trava (holder_pid volta a NULL).
    conn = tmp_db
    raw, main = _make_raw(data_root)
    import_classroom(raw, "Turma X", main)
    assert _holder_pid(conn) is None

