"""Estágio E (service) — integração do orquestrador impuro (D-06/D-13/Lock Timing).

Cobre o comportamento de BORDA que os estágios puros (planos 02-04) não exercitam: o commit
atômico (D-06 — falha no meio não deixa resto), o round-trip de colunas do Parquet (D-13 — o
seam do edmkt_core), a preservação do cru (D-13) e a trava global (Lock Timing — busy não
persiste, release garantido sob exceção). Herméticos, CPU-only, sobre `tmp_db` + tmp_path;
NUNCA o CSEDM real (Pitfall 2). As asserções pinam invariantes (0 linhas / colunas do seam /
holder NULL), nunca valores mágicos de AUC. Espelha o estilo de rollback de test_artifacts.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from edmkt_app import settings
from edmkt_app.ingestion import clean, service
from edmkt_app.persistence import repositories as repos

# MainTable com DUAS classes nos first-attempts (≥1 acerto E ≥1 erro) ⇒ assignment trainable
# (D-09). CodeStateID casa 1:1 com o CodeStates.csv abaixo (sem órfãos neste fixture base).
_MAIN_TABLE = (
    "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp\n"
    "S1,439,1,c1,Run.Program,0.0,2019-03-01T08:00:00Z\n"
    "S1,439,2,c2,Run.Program,1.0,2019-03-01T08:01:00Z\n"
    "S2,439,1,c3,Run.Program,1.0,2019-03-01T08:02:00Z\n"
    "S2,439,2,c4,Run.Program,0.5,2019-03-01T08:03:00Z\n"
)

# CodeStates: o snapshot Java por CodeStateID. O `Code` deve sobreviver SÓ no Parquet, nunca
# no SQLite (T-03-16). Score 0.5 acima fica preservado contínuo (Pitfall 4).
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


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    """Aponta service.DATA_ROOT para tmp_path — escrita de Parquet/raw fica hermética."""
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    return tmp_path


def _counts(conn) -> tuple[int, int, int]:
    t = conn.execute("SELECT COUNT(*) AS n FROM classroom;").fetchone()["n"]
    a = conn.execute("SELECT COUNT(*) AS n FROM assignment;").fetchone()["n"]
    s = conn.execute("SELECT COUNT(*) AS n FROM submission;").fetchone()["n"]
    return t, a, s


def _holder_pid(conn):
    return conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()["holder_pid"]


# --- happy path: persiste Turma + Assignments + Submissions + Parquet (D-13) ---------------


def test_happy_persists_turma_assignment_submissions_and_parquet(tmp_db, data_root):
    conn = tmp_db
    raw, main = _make_raw(data_root)

    report = service.ingest(conn, raw, "Turma X", main)

    assert not report.has_fatal
    n_turmas, n_assign, n_sub = _counts(conn)
    assert n_turmas == 1
    assert n_assign == 1  # um único AssignmentID (439) no fixture
    assert n_sub == 4  # 4 eventos Run.Program, todos com snapshot (sem órfão)

    # Assignment ganhou status do gate (D-08): ambas as classes presentes ⇒ trainable.
    status = conn.execute("SELECT status FROM assignment;").fetchone()["status"]
    assert status == "ready_for_kc_generation"

    # Parquet do stream canônico existe em clean/ com o nome derivado do AssignmentID (não do zip).
    pq = data_root / "turma-x" / "clean" / "assignment_439.parquet"
    assert pq.exists()


def test_detect_variants_does_not_acquire_lock(tmp_db, data_root, tmp_path):
    # detect_variants é read-only sobre o estado compartilhado (Lock Timing): extrai o zip e
    # lista variantes sem NUNCA setar holder_pid. Montamos um zip mínimo para extrair.
    import zipfile

    conn = tmp_db
    src = tmp_path / "upload.zip"
    with zipfile.ZipFile(src, "w") as zf:
        zf.writestr("MainTable.csv", _MAIN_TABLE)
        zf.writestr("CodeStates/CodeStates.csv", _CODE_STATES)

    variants = service.detect_variants(src, "turma-x")

    assert variants["main_tables"]  # achou ao menos uma MainTable
    assert variants["raw_dir"].exists()  # cru preservado em raw/ (D-13)
    # Detecção NÃO toca a trava — holder_pid segue NULL.
    assert _holder_pid(conn) is None


# --- D-13: round-trip de colunas + Score contínuo + Code só no Parquet ---------------------


def test_parquet_roundtrip_columns_and_score_continuous(tmp_db, data_root):
    conn = tmp_db
    raw, main = _make_raw(data_root)
    service.ingest(conn, raw, "Turma X", main)

    pq = data_root / "turma-x" / "clean" / "assignment_439.parquet"
    back = pd.read_parquet(pq)

    # As 9 colunas do seam edmkt_core, exatamente (D-13).
    assert set(back.columns) == set(clean.CANONICAL_COLUMNS)
    # Score contínuo preservado: o 0.5 não foi destruído na binarização (Pitfall 4).
    assert 0.5 in set(back["score"].tolist())
    # Code presente no Parquet (é o snapshot do treino/EDA).
    assert back["code"].notna().all()


def test_code_absent_from_sqlite_submission(tmp_db, data_root):
    # Information Disclosure (T-03-16): o Code cru do aluno NUNCA entra no SQLite — a tabela
    # submission sequer tem coluna Code. Score cru contínuo, sim, está lá.
    conn = tmp_db
    raw, main = _make_raw(data_root)
    service.ingest(conn, raw, "Turma X", main)

    cols = {r["name"] for r in conn.execute("PRAGMA table_info(submission);").fetchall()}
    assert "code" not in {c.lower() for c in cols}
    scores = [r["score"] for r in conn.execute("SELECT score FROM submission;").fetchall()]
    assert 0.5 in scores  # cru contínuo preservado no SQLite


def test_raw_csv_preserved_after_ingest(tmp_db, data_root):
    # D-13: o cru continua em raw/ pós-ingest (reprodutibilidade / re-ingest).
    conn = tmp_db
    raw, main = _make_raw(data_root)
    service.ingest(conn, raw, "Turma X", main)
    assert main.exists()
    assert (raw / "CodeStates" / "CodeStates.csv").exists()


# --- D-06: commit atômico (falha no meio não deixa resto) ----------------------------------


def test_atomicity_failure_mid_persist_leaves_nothing(tmp_db, data_root, monkeypatch):
    # Falha dura DEPOIS do Parquet escrito e no meio dos INSERTs: o ROLLBACK desfaz o SQLite e
    # o service remove o Parquet recém-escrito (rmtree/unlink) — espelha test_artifacts CR-01.
    conn = tmp_db
    raw, main = _make_raw(data_root)

    real_insert = repos.SubmissionRepository.insert
    calls = {"n": 0}

    def _fail_on_second(self, submission):
        calls["n"] += 1
        if calls["n"] == 2:  # deixa o 1º INSERT passar, falha no 2º (meio da persistência)
            raise sqlite3.OperationalError("disk full at submission INSERT (simulado)")
        return real_insert(self, submission)

    monkeypatch.setattr(repos.SubmissionRepository, "insert", _fail_on_second)

    with pytest.raises(sqlite3.OperationalError):
        service.ingest(conn, raw, "Turma X", main)

    # SQLite inalterado: 0 turmas/assignments/submissions (ROLLBACK).
    assert _counts(conn) == (0, 0, 0)
    # Nenhum Parquet remanescente (unlink no rollback) — sem dataset meio-gravado.
    pq = data_root / "turma-x" / "clean" / "assignment_439.parquet"
    assert not pq.exists()
    # Release garantido mesmo sob exceção: a trava voltou a NULL (SC3 / Lock Timing).
    assert _holder_pid(conn) is None


def test_fatal_preflight_persists_nothing(tmp_db, data_root):
    # Coluna obrigatória ausente ⇒ has_fatal True e NADA persiste (D-05 nível 1 / D-06).
    conn = tmp_db
    bad_main = (
        "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,ServerTimestamp\n"  # sem Score
        "S1,439,1,c1,Run.Program,2019-03-01T08:00:00Z\n"
    )
    raw, main = _make_raw(data_root, main_table=bad_main)

    report = service.ingest(conn, raw, "Turma X", main)

    assert report.has_fatal
    assert _counts(conn) == (0, 0, 0)
    # Pré-voo aborta antes da persistência: nenhum diretório clean/ criado.
    assert not (data_root / "turma-x" / "clean").exists()


# --- Lock Timing: busy não persiste; release garantido --------------------------------------


def test_lock_busy_does_not_persist(tmp_db, data_root):
    # Trava ocupada por um PID VIVO (o próprio processo de teste) ⇒ ingest devolve "busy" e
    # NADA persiste (turma count inalterado). Não removemos a trava de outro dono.
    conn = tmp_db
    raw, main = _make_raw(data_root)
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='ingestion', "
        "acquired_at='2026-06-21T00:00:00Z' WHERE id=1;",
        (os.getpid(),),
    )

    report = service.ingest(conn, raw, "Turma X", main)

    assert report.has_fatal  # relatório "busy" carrega um item fatal
    assert any(i.check == "pipeline_busy" for i in report.items)
    assert _counts(conn) == (0, 0, 0)
    # A trava do dono vivo NÃO foi tocada por nós.
    assert _holder_pid(conn) == os.getpid()


def test_lock_released_after_successful_ingest(tmp_db, data_root):
    # Após um ingest bem-sucedido, o `with lock` libera a trava (holder_pid volta a NULL).
    conn = tmp_db
    raw, main = _make_raw(data_root)
    service.ingest(conn, raw, "Turma X", main)
    assert _holder_pid(conn) is None


# --- B2: um re-ingest que falha não pode destruir o Parquet que estava lá ------------


def test_failed_reingest_preserves_the_previous_parquet(tmp_db, data_root, monkeypatch):
    """`to_parquet` sobrescreve. Se a persistência falhar depois disso, o rollback antigo dava
    `unlink` no arquivo — que já havia substituído o bom. A turma ficava SEM Parquet nenhum.

    A nota de projeto dizia que usar unlink em vez de rmtree "preserva datasets de uploads
    anteriores": preserva os de OUTROS assignments, não o que está sendo sobrescrito.
    """
    conn = tmp_db
    raw, main = _make_raw(data_root)
    service.ingest(conn, raw, "Turma X", main)

    pq = data_root / "turma-x" / "clean" / "assignment_439.parquet"
    original = pq.read_bytes()

    # Segunda ingestão que estoura DEPOIS do blob, durante os INSERTs.
    def _boom(self, submission):
        raise RuntimeError("falha simulada no meio da persistência")

    monkeypatch.setattr(repos.SubmissionRepository, "insert", _boom)
    with pytest.raises(RuntimeError):
        service.ingest(conn, raw, "Turma X", main)

    assert pq.exists(), "o Parquet anterior foi destruído por um re-ingest que falhou"
    assert pq.read_bytes() == original
    assert not list(pq.parent.glob("*.tmp")), "restou temporário do write interrompido"
