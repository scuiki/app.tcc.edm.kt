"""Shared pytest fixtures for the edmkt_core suite.

The `a439_mini` fixture is a SYNTHETIC, hermetic ProgSnap2-shaped DataFrame (D-11/D-12):
it is generated in code, never loaded from the real CSEDM, and no test asserts a specific
AUC against it. The real-data check lives in the regression test against the TCC 1 reference
run (plan 06, marked `regression`, gated on EDMKT_CSEDM_PATH).
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest
import torch

ASSIGNMENT_ID = 439


def _resolve_csedm_path() -> Path:
    """Resolve EDMKT_CSEDM_PATH or skip the regression test with a clear reason (D-07/D-12).

    The real CSEDM is NEVER copied into the repo and NEVER read from ../tcc.edm.kt/data
    (D-12); the operator points EDMKT_CSEDM_PATH at the provisioned dataset on nitro. When
    it is unset (or the dir/MainTable is missing) the regression test skips cleanly rather than
    erroring, so the default fast suite stays green on machines without the dataset.
    """
    raw = os.environ.get("EDMKT_CSEDM_PATH")
    if not raw:
        pytest.skip(
            "EDMKT_CSEDM_PATH unset — regression test skipped (D-07 fast-by-default). "
            "Set it to the provisioned CSEDM dir (with MainTable.csv + CodeStates/) to run."
        )
    data_dir = Path(raw)
    if not (data_dir / "MainTable.csv").exists():
        pytest.skip(f"EDMKT_CSEDM_PATH={data_dir} has no MainTable.csv — regression test skipped.")
    return data_dir

# Minimal compilable Java member declarations — javalang.parse_member_declaration
# parses these and extract_paths_javalang yields >= 1 AST path.
_JAVA_OK_A = "public int f(int x) { return x + 1; }"
_JAVA_OK_B = "public int g(int a, int b) { int s = a + b; return s; }"
_JAVA_OK_C = "public boolean h(int n) { if (n > 0) { return true; } return false; }"
# Deliberately malformed Java — exercises the try/except DoS guard (returns []).
_JAVA_BAD = "public int oops( { return ;;; }"
# Parses (parse_member_declaration accepts it) but has no leaf pairs, so
# extract_paths_javalang returns [] WITHOUT raising — the parsed_sem_paths case
# that the 3-way classifier must separate from parse_failed (D-09).
_JAVA_EMPTY_CLASS = "class C {}"


def _row(subject, problem, ts, event, score, code, csid):
    """One ProgSnap2 event row. `correct` follows the Code-DKT label rule:
    Run.Program with Score == 1.0 (Compile.Error never counts as correct)."""
    correct = int(event == "Run.Program" and score == 1.0)
    return {
        "SubjectID": subject,
        "ProblemID": problem,
        "AssignmentID": ASSIGNMENT_ID,
        "ServerTimestamp": ts,
        "EventType": event,
        "Score": score,
        "CodeStateID": csid,
        "Code": code,
        "correct": correct,
    }


@pytest.fixture
def a439_mini() -> pd.DataFrame:
    """Synthetic A439 ProgSnap2 subset.

    Guarantees:
      - 3 students across 3 problems (1, 2, 3).
      - EventType in {Run.Program, Compile.Error}; Score in {0.0, 1.0}.
      - Monotonic ServerTimestamp within each student.
      - Student "S_long" has > max_len(=5 in tests) events so truncation is exercised.
      - Problem 1 is repeated for every student, so is_first_attempt carries both
        True (first occurrence) and False (later occurrence) rows.
      - At least one malformed-Java snapshot to characterize the parser guard.
    """
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []

    def ts(student_offset, step):
        # distinct, monotonic-per-student timestamps
        return base + pd.Timedelta(hours=student_offset) + pd.Timedelta(minutes=step)

    # Student S1: problem 1 attempted twice (first fail, then pass) -> repeated problem.
    rows += [
        _row("S1", 1, ts(0, 0), "Run.Program", 0.0, _JAVA_OK_A, "c1"),
        _row("S1", 1, ts(0, 1), "Run.Program", 1.0, _JAVA_OK_A, "c2"),
        _row("S1", 2, ts(0, 2), "Run.Program", 1.0, _JAVA_OK_B, "c3"),
    ]

    # Student S2: a Compile.Error (malformed Java) then a passing run on problem 1,
    # plus problem 3 — repeated problem 1 again across the cohort.
    rows += [
        _row("S2", 1, ts(1, 0), "Compile.Error", 0.0, _JAVA_BAD, "c4"),
        _row("S2", 1, ts(1, 1), "Run.Program", 1.0, _JAVA_OK_A, "c5"),
        _row("S2", 3, ts(1, 2), "Run.Program", 0.0, _JAVA_OK_C, "c6"),
    ]

    # Student S_long: 8 events on problems 1/2/3 (> max_len=5) so truncation triggers,
    # with problem repetitions both inside and across the truncation window.
    long_plan = [
        (1, "Run.Program", 0.0, _JAVA_OK_A, "l1"),
        (2, "Run.Program", 0.0, _JAVA_OK_B, "l2"),
        (1, "Run.Program", 1.0, _JAVA_OK_A, "l3"),
        (3, "Run.Program", 0.0, _JAVA_OK_C, "l4"),
        (2, "Run.Program", 1.0, _JAVA_OK_B, "l5"),
        (3, "Run.Program", 1.0, _JAVA_OK_C, "l6"),
        (1, "Run.Program", 1.0, _JAVA_OK_A, "l7"),
        (2, "Run.Program", 1.0, _JAVA_OK_B, "l8"),
    ]
    for step, (pid, event, score, code, csid) in enumerate(long_plan):
        rows.append(_row("S_long", pid, ts(2, step), event, score, code, csid))

    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")
    return df


@pytest.fixture
def csedm_main_table() -> pd.DataFrame:
    """Real CSEDM Spring 2019 events, shaped for the public train_and_evaluate seam.

    Reads EDMKT_CSEDM_PATH (skip-if-unset, D-07/D-12) and reproduces the TCC 1 Code-DKT
    input exactly: Run.Program events only (the BKT/DKT filter the Code-DKT regression test
    consumed — sequences_bkt_dkt.pkl, notebook 06 cell 4 asserts EventType == Run.Program),
    correct = (Score == 1.0), the per-row Java snapshot joined from CodeStates.csv on
    CodeStateID, and types normalized like data_loader.load_spring2019_split
    (ServerTimestamp -> UTC datetime, AssignmentID/ProblemID -> Int64).

    split_by_subject(random_state=1, min_attempts=3) then reproduces the reference
    partition (Pitfall 3); the Code column flows into _code_states_from_df and `correct`
    into build_code_input_tensor/predict.
    """
    data_dir = _resolve_csedm_path()

    df = pd.read_csv(data_dir / "MainTable.csv")
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True, errors="coerce")
    df["AssignmentID"] = pd.to_numeric(df["AssignmentID"], errors="coerce").astype("Int64")
    df["ProblemID"] = pd.to_numeric(df["ProblemID"], errors="coerce").astype("Int64")

    # Run.Program only + binary label (data_loader.filter_for_bkt_dkt — the exact filter
    # behind sequences_bkt_dkt.pkl that the TCC 1 Code-DKT run trained on).
    df = df[df["EventType"] == "Run.Program"].copy()
    df["correct"] = (df["Score"] == 1.0).astype(int)

    # Join the Java snapshot per event (CodeStateID -> Code) so the pure-DataFrame seam
    # (_code_states_from_df) sees inline code without reading a CSEDM path itself (CORE-01).
    code_states = pd.read_csv(data_dir / "CodeStates" / "CodeStates.csv")
    code_map = dict(zip(code_states["CodeStateID"].astype(str), code_states["Code"].fillna("")))
    df["Code"] = df["CodeStateID"].astype(str).map(code_map).fillna("")

    return df.reset_index(drop=True)


@pytest.fixture
def cpu_device() -> torch.device:
    """Force CPU so unit/characterization tests never touch the GPU (D-02)."""
    return torch.device("cpu")


# --- Phase 2 persistence fixtures (shared by the Wave 2 plans) -------------------
# Synthetic + hermetic, mirroring a439_mini: built in code, never touching the GPU,
# real CSEDM, or a persistent app.db. Defined here so the parallel Wave 2 plans
# (repositories/artifacts/lock/flip) consume one conftest instead of racing edits.


@pytest.fixture
def tmp_db(tmp_path):
    """A migrated app.db on tmp_path: connect() + run_migrations(), schema at user_version=1."""
    from edmkt_app import settings
    from edmkt_app.persistence import connect, run_migrations

    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    return conn


@pytest.fixture
def tiny_model() -> torch.nn.Module:
    """A minuscule nn.Module standing in for a trained Code-DKT — NOT trained.

    Carries the two attributes the artifact reload contract derives from the live
    object (RESEARCH Open Q1 / Pitfall 1): `.input_dim` and `.fc.out_features`.
    """

    class _TinyModel(torch.nn.Module):
        def __init__(self, input_dim: int = 3, output_dim: int = 2):
            super().__init__()
            self.input_dim = input_dim
            self.fc = torch.nn.Linear(input_dim, output_dim)

    return _TinyModel()


@pytest.fixture
def tiny_vocab() -> dict:
    """Synthetic vocab mapping shaped like the train_and_evaluate vocab (node/path maps)."""
    return {
        "token_to_idx": {"<PAD>": 0, "<UNK>": 1, "if": 2, "return": 3},
        "path_to_idx": {"<PAD>": 0, "<UNK>": 1, "a->b": 2},
        "node_count": 4,
        "path_count": 3,
    }


@pytest.fixture
def tiny_config() -> dict:
    """Flat FROZEN_CONFIG-style mapping with the args the reload reconstructs."""
    return {
        "hidden_dim": 8,
        "dropout": 0.1,
        "R": 4,
        "node_embed_dim": 6,
        "path_embed_dim": 6,
    }


# --- Phase 3 ingestion fixtures (shared by the Wave 2 pure-logic plans) -----------
# Synthetic + hermetic like a439_mini — NEVER the real CSEDM (Pitfall 2). Each fixture
# exercises an edge case that has ZERO coverage in the reference dataset (orphan CodeStateID,
# single-class assignment, BOM, tolerant layout), so the discover/validate/clean/viability
# plans can pin those behaviors without the real data.


@pytest.fixture
def ingest_orphan_df() -> tuple[pd.DataFrame, dict[str, str]]:
    """Stream cru + code_states com ≥1 CodeStateID órfão (D-11): um evento aponta para um
    CodeStateID ausente em CodeStates, exercitando o descarte+contagem do clean (0 cobertura
    no dataset de referência). Devolve (df, code_states) — o clean faz o join Code via code_states."""
    code_states = {"c1": _JAVA_OK_A, "c2": _JAVA_OK_B}  # "c_orphan" deliberadamente AUSENTE
    rows = [
        _row("S1", 1, "2019-03-01T08:00:00Z", "Run.Program", 1.0, _JAVA_OK_A, "c1"),
        _row("S1", 2, "2019-03-01T08:01:00Z", "Run.Program", 0.0, _JAVA_OK_B, "c2"),
        _row("S2", 1, "2019-03-01T08:02:00Z", "Run.Program", 1.0, "", "c_orphan"),  # órfão
    ]
    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")
    return df, code_states


@pytest.fixture
def ingest_single_class_df() -> pd.DataFrame:
    """Assignment cujos first-attempts têm UMA classe só (todos Score==1.0) → AUC indefinido
    → bloqueio duro de viabilidade (D-09, único bloqueio científico). Sem a outra classe,
    both_classes_present é False."""
    rows = [
        _row("S1", 1, "2019-03-01T08:00:00Z", "Run.Program", 1.0, _JAVA_OK_A, "c1"),
        _row("S2", 1, "2019-03-01T08:01:00Z", "Run.Program", 1.0, _JAVA_OK_A, "c2"),
        _row("S3", 2, "2019-03-01T08:02:00Z", "Run.Program", 1.0, _JAVA_OK_B, "c3"),
    ]
    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")
    return df


@pytest.fixture
def ingest_bom_csv(tmp_path) -> Path:
    """MainTable.csv gravado com BOM UTF-8 (encoding='utf-8-sig'): o validate lê com
    utf-8-sig (BOM consumido transparente → warning, NÃO fatal — D-05 nível 2)."""
    main = tmp_path / "MainTable.csv"
    main.write_text(
        "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp\n"
        "S1,439,1,c1,Run.Program,1.0,2019-03-01T08:00:00Z\n",
        encoding="utf-8-sig",  # prefixa o BOM (﻿) no arquivo
    )
    return main


# --- Phase 4 feature-cache fixtures (plan 04-02) ----------------------------------
# Synthetic + hermetic like a439_mini: code-built snippets keyed by CodeStateID, never
# the real CSEDM. The cache wrapper namespaces files per turma and skips re-extraction
# on a hit; these feed the incremental-skip / namespace / no-leak / traversal tests.


@pytest.fixture
def cache_config() -> dict:
    """FROZEN_CONFIG-shaped path-extraction args the cache wrapper forwards to build_cache
    (Shi et al. 2022 reproducibility: R=50, max_path_length=8, max_path_width=2, seed=42)."""
    return {"max_path_length": 8, "max_path_width": 2, "R": 50, "seed": 42}


@pytest.fixture
def cache_code_states() -> dict[str, str]:
    """{CodeStateID: Java} mixing every parse class so one fixture drives all cache tests:
    com_paths (c_ok*), parsed_sem_paths (c_empty), parse_failed (c_bad), no_code (c_blank)."""
    return {
        "c_ok1": _JAVA_OK_A,
        "c_ok2": _JAVA_OK_B,
        "c_empty": _JAVA_EMPTY_CLASS,
        "c_bad": _JAVA_BAD,
        "c_blank": "   ",
    }


# --- Phase 4 FastAPI fixtures (plan 04-04) ----------------------------------------
# Primeira camada HTTP do projeto: TestClient sobre create_app(), com o app.db em tmp_path
# e DATA_ROOT redirecionado para o tmp — herméticos, sem rede nem app.db persistente.


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    """TestClient sobre create_app() com app.db migrado em tmp_path + DATA_ROOT hermético.

    O lifespan resolve o db_path por EDMKT_DB_PATH; apontamos para tmp_path/app.db e
    redirecionamos service.DATA_ROOT para a mesma raiz tmp. O `with TestClient(...)` dispara
    startup/shutdown (roda migrations + reclaim no startup). Devolve (client, conn) onde conn
    é uma conexão de teste separada para o mesmo app.db (caminho de leitura WAL).
    """
    from fastapi.testclient import TestClient

    from edmkt_app.api import create_app
    from edmkt_app import settings
    from edmkt_app.persistence import connect

    db_path = tmp_path / "app.db"
    monkeypatch.setenv("EDMKT_DB_PATH", str(db_path))
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)

    app = create_app()
    with TestClient(app) as client:
        conn = connect(str(db_path))
        try:
            yield client, conn
        finally:
            conn.close()


# --- Phase 6 mastery fixtures (plan 06-01) ----------------------------------------
# Cross-cutting Wave 0 dependency: o fixture trained_artifact persiste um CodeDKTModel
# MINÚSCULO via ArtifactStore (não o tiny_model stand-in — load_version reconstrói um
# CodeDKTModel de verdade), semeia uma Q-matrix determinística (problem→KC) + KCs, e
# expõe tudo que os planos de mastery-core/API precisam p/ uma matriz aluno×KC
# determinística. Sintético/hermético: CPU-only, sob tmp_path, NUNCA o CSEDM real.


@pytest.fixture
def trained_artifact(tmp_db, tmp_path, tiny_vocab, tiny_config):
    """Artefato Code-DKT minúsculo persistido + Q-matrix/KC determinísticos (DASH-01/02/03/05).

    NÃO é treinado: os pesos vêm de seed fixa (set_global_seed), não de um treino real — a
    matriz aluno×KC daqui é determinística e reproduzível, não um AUC realista (o teste de regressão
    é o oráculo de numerics). Persiste via ArtifactStore.persist para que load_version
    (artifacts.py:142) reconstrua o CodeDKTModel com weights_only=True. Q-matrix: 3 problemas
    (1,2,3) → 2 KCs, com o problema 3 ligado a ambos os KCs, exercitando a média problem→KC.

    Devolve um namespace com: conn (DB migrado), turma_id, assignment_id (id DB), artifact_id,
    version_number, artifact_dir, kcs (list[KC] com ids DB), qmatrix (list[QMatrix]) e o store.
    """
    from edmkt_app.persistence import models
    from edmkt_app.persistence import repositories as repos
    from edmkt_app.persistence.artifacts import ArtifactStore
    from edmkt_core.models.code_dkt import CodeDKTModel
    from edmkt_core.seeding import set_global_seed

    conn = tmp_db
    now = "2026-06-21T00:00:00Z"

    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name="Turma 6", created_at=now)
    )
    assignment_id = repos.AssignmentRepository(conn).insert(
        models.Assignment(
            id=None,
            turma_id=turma_id,
            name="A439",
            current_version_id=None,
            created_at=now,
            status="kc_approved",
        )
    )

    # CodeDKTModel real, dims minúsculas — n_problems(M)=3, input_dim=2M (code_dkt.py:148,150),
    # embeddings/hidden pequenos p/ rodar instantâneo na CPU. Pesos de seed fixa, não treinados.
    set_global_seed(42, strict=False)
    M = 3
    model = CodeDKTModel(
        input_dim=2 * M,
        hidden_dim=tiny_config["hidden_dim"],
        output_dim=M,
        node_count=tiny_vocab["node_count"],
        path_count=tiny_vocab["path_count"],
        dropout=tiny_config["dropout"],
        R=tiny_config["R"],
        node_embed_dim=tiny_config["node_embed_dim"],
        path_embed_dim=tiny_config["path_embed_dim"],
    )

    # Mesma raiz que train.py/mastery_service montam: DATA_ROOT/<turma_slug>/models. Os testes
    # apontam DATA_ROOT para tmp_path, e a turma "Turma 6" vira o slug "turma-6".
    store = ArtifactStore(str(tmp_path / "turma-6" / "models"))
    persisted = store.persist(conn, turma_id, assignment_id, model, tiny_vocab, tiny_config)
    artifact_id = persisted["artifact_id"]
    # Publica o ponteiro current_version_id — o caminho de leitura do dashboard segue daqui
    # (assignment.current_version_id → model_artifact → artifact_dir → load_version).
    from edmkt_app.persistence.artifacts import flip_current

    flip_current(conn, assignment_id, artifact_id)

    # Q-matrix determinística: problemas 1,2,3 → KC1/KC2; o problema 3 liga AMBOS os KCs,
    # forçando a média problem→KC (Pitfall 2: KC-mastery = mean sobre os problemas do KC).
    kc_repo = repos.KCRepository(conn)
    kc1 = kc_repo.insert(models.KC(id=None, assignment_id=assignment_id, name="Laços", kc_index=0))
    kc2 = kc_repo.insert(
        models.KC(id=None, assignment_id=assignment_id, name="Condicionais", kc_index=1)
    )
    qm_repo = repos.QMatrixRepository(conn)
    bindings = [(kc1, 1), (kc1, 3), (kc2, 2), (kc2, 3)]
    for kc_id, problem_id in bindings:
        qm_repo.insert(
            models.QMatrix(id=None, assignment_id=assignment_id, kc_id=kc_id, problem_id=problem_id)
        )

    kcs = kc_repo.list_by_assignment(assignment_id)
    qmatrix = qm_repo.list_by_assignment(assignment_id)

    class _TrainedArtifact:
        pass

    ns = _TrainedArtifact()
    ns.conn = conn
    ns.turma_id = turma_id
    ns.assignment_id = assignment_id
    ns.artifact_id = artifact_id
    ns.version_number = persisted["version_number"]
    ns.artifact_dir = persisted["dir"]
    ns.kcs = kcs
    ns.qmatrix = qmatrix
    ns.store = store
    ns.model = model
    ns.vocab = tiny_vocab
    ns.config = tiny_config
    return ns


# --- Phase 5 KC pipeline fixtures (plan 05-01) ------------------------------------
# Artefatos de referência do KCGen-KT: os artefatos REAIS do TCC 1 (A439) copiados de
# ../tcc.edm.kt/results/ para tests/data/kc/. Nenhum teste chama o `claude` real — o
# transporte é sempre monkeypatchado (subprocess.run/Popen). `fake_claude_envelope` constrói
# o envelope JSON verificado ao vivo no host (05-RESEARCH §Pattern 1) para esses mocks.


@pytest.fixture
def kc_reference_dir() -> Path:
    """Path para tests/data/kc — os 4 artefatos de referência do TCC 1 (kc_raw/kc_clusters/
    kc_descriptions/qmatrix _A439), usados pelo replay de referência do pipeline puro (KC-01)."""
    return Path(__file__).resolve().parent / "data" / "kc"


@pytest.fixture
def fake_claude_envelope():
    """Constrói o envelope JSON que `claude -p --output-format json` devolve (verificado ao
    vivo, 05-RESEARCH §Pattern 1). Os testes monkeypatcham subprocess.run para devolver
    json.dumps(envelope) no stdout, sem nunca chamar o binário real nem gastar cota."""

    def _build(structured_output, result: str = "") -> dict:
        return {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": result,
            "structured_output": structured_output,
        }

    return _build


@pytest.fixture
def ingest_layout_dir(tmp_path) -> Path:
    """Árvore com CodeStates em LinkTables/ (variante CodeWorkout de referência — D-02) + múltiplas
    MainTable (All/ e Train/ — D-03 → professor escolhe). Exercita o glob tolerante do
    discover sem reorganização manual."""
    (tmp_path / "LinkTables").mkdir()
    (tmp_path / "LinkTables" / "CodeStates.csv").write_text(
        "CodeStateID,Code\nc1,\"public int f(){return 1;}\"\n", encoding="utf-8"
    )
    for variant in ("All", "Train"):
        (tmp_path / variant).mkdir()
        (tmp_path / variant / "MainTable.csv").write_text(
            "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp\n"
            "S1,439,1,c1,Run.Program,1.0,2019-03-01T08:00:00Z\n",
            encoding="utf-8",
        )
    return tmp_path
