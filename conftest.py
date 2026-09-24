"""Fixtures compartilhadas da suíte.

Na raiz do repositório para valer tanto para os testes ao lado dos arquivos (src/) quanto para
tests/. O `a439_mini` é SINTÉTICO e hermético: gerado em código, nunca lido do CSEDM real, e nenhum
teste afirma um AUC específico sobre ele. O dado real fica no teste de regressão contra o TCC 1
(tests/test_regression_a439.py).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
import torch
from api.assignments.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.domain.entities.classroom_entity import Classroom
from api.assignments.domain.entities.assignment_entity import Assignment

# Fixtures que montam cada funcionalidade com a infraestrutura real (ver tests/fixtures/).
pytest_plugins = ["tests.fixtures.classroom_import", "tests.fixtures.mastery_dashboard"]

ASSIGNMENT_ID = 439


# Minimal compilable Java member declarations — javalang.parse_member_declaration
# parses these and extract_ast_paths yields >= 1 AST path.
_JAVA_OK_A = "public int f(int x) { return x + 1; }"
_JAVA_OK_B = "public int g(int a, int b) { int s = a + b; return s; }"
_JAVA_OK_C = "public boolean h(int n) { if (n > 0) { return true; } return false; }"
# Deliberately malformed Java — exercises the try/except DoS guard (returns []).
_JAVA_BAD = "public int oops( { return ;;; }"
# Parses (parse_member_declaration accepts it) but has no leaf pairs, so
# extract_ast_paths returns [] WITHOUT raising — the parsed_sem_paths case
# that the 3-way classifier must separate from parse_failed (D-09).
_JAVA_EMPTY_CLASS = "class C {}"


def _row(subject, problem, ts, event, score, code, snapshot_id):
    """One cleaned event row (glossary column names). `is_correct` follows the Code-DKT label
    rule: Run.Program with score == 1.0 (Compile.Error never counts as correct)."""
    is_correct = int(event == "Run.Program" and score == 1.0)
    return {
        "student_id": subject,
        "problem_id": problem,
        "progsnap_assignment_id": ASSIGNMENT_ID,
        "submitted_at": ts,
        "event_type": event,
        "score": score,
        "code_snapshot_id": snapshot_id,
        "code": code,
        "is_correct": is_correct,
    }


def _typed(df: pd.DataFrame) -> pd.DataFrame:
    """The dtypes the cleaned events carry (UTC timestamps, nullable ints for the ids)."""
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")
    return df


def _as_progsnap_upload(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Cleaned events back to the shape of the teacher's upload: the ProgSnap2 column names and
    no derived `is_correct`. Input for the tests of the import boundary (ingestion/clean)."""
    from api.classroom_import.domain.services.submission_cleaning import PROGSNAP_TO_CLEANED_COLUMNS

    to_progsnap = {new: old for old, new in PROGSNAP_TO_CLEANED_COLUMNS.items()}
    return cleaned.drop(columns=["is_correct"]).rename(columns=to_progsnap)


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
    for step, (pid, event, score, code, snapshot_id) in enumerate(long_plan):
        rows.append(_row("S_long", pid, ts(2, step), event, score, code, snapshot_id))

    return _typed(pd.DataFrame(rows))


@pytest.fixture
def a439_mini_progsnap(a439_mini) -> pd.DataFrame:
    """The same events as `a439_mini`, as they arrive in the teacher's ProgSnap2 upload."""
    return _as_progsnap_upload(a439_mini)


@pytest.fixture
def data_root(tmp_path, monkeypatch) -> Path:
    """Aponta a raiz de dados para tmp_path: tudo o que se grava em data/ fica hermético."""
    from api.shared.infrastructure import settings

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def java_snippets() -> SimpleNamespace:
    """Os trechos de Java dos fixtures, para testes que precisam de um código de cada classe de parse."""
    return SimpleNamespace(
        ok_a=_JAVA_OK_A, ok_b=_JAVA_OK_B, ok_c=_JAVA_OK_C, bad=_JAVA_BAD, empty_class=_JAVA_EMPTY_CLASS
    )


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
    from api.shared.infrastructure import settings
    from api.shared.infrastructure.database.migrations.runner import run_migrations
    from api.shared.infrastructure.database.sqlite_connection import connect

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
    """Flat CODE_DKT_HYPERPARAMETERS-style mapping with the args the reload reconstructs."""
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
    return _as_progsnap_upload(_typed(pd.DataFrame(rows))), code_states


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
    return _typed(pd.DataFrame(rows))


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
    """CODE_DKT_HYPERPARAMETERS-shaped path-extraction args the cache wrapper forwards to extract_ast_paths_for_snapshots
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

    from api.main import create_app
    from api.shared.infrastructure import settings
    from api.shared.infrastructure.database.sqlite_connection import connect

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
# MINÚSCULO via TrainedModelFileStore (não o tiny_model stand-in — load_version reconstrói um
# CodeDKTModel de verdade), semeia uma Q-matrix determinística (problem→KC) + KCs, e
# expõe tudo que os planos de mastery-core/API precisam p/ uma matriz aluno×KC
# determinística. Sintético/hermético: CPU-only, sob tmp_path, NUNCA o CSEDM real.


@pytest.fixture
def trained_artifact(tmp_db, data_root, tiny_vocab, tiny_config):
    """Artefato Code-DKT minúsculo persistido + Q-matrix/KC determinísticos (DASH-01/02/03/05).

    NÃO é treinado: os pesos vêm de semente fixa, não de um treino real; a matriz aluno × KC daqui
    é determinística, não um AUC realista (o oráculo da numérica é o teste de regressão). Grava pela
    TrainedModelFileStore real, para a leitura reconstruir o CodeDKTModel com weights_only=True.
    Q-matrix: 3 problemas → 2 KCs, com o problema 3 ligado aos dois (a média problema → KC).

    Devolve um namespace com: conn, classroom_id, assignment_id (id do banco), artifact_id,
    version_number, artifact_dir, kcs, qmatrix, store, model, vocab e config.
    """
    import pandas as pd

    from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
    from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId
    from api.model_training.domain.code_dkt_trainer import TrainingOutcome
    from api.model_training.domain.training_dataset import TrainingDataset
    from api.model_training.infrastructure.sqlite_trained_model_repository import (
        SqliteTrainedModelRepository,
    )
    from api.model_training.infrastructure.trained_model_file_store import TrainedModelFileStore
    from ml.code_dkt.model import CodeDKTModel
    from ml.reproducibility.random_seed import seed_all_random_generators

    conn = tmp_db
    now = "2026-06-21T00:00:00Z"

    classroom_id = SqliteClassroomRepository(conn).add(
        Classroom(id=None, name="Turma 6", created_at=now)
    )
    assignment_id = SqliteAssignmentRepository(conn).add(
        Assignment(
            id=None,
            classroom_id=classroom_id,
            name="A439",
            progsnap_assignment_id=439,
            published_model_id=None,
            created_at=now,
            status="kc_approved",
        )
    )

    # CodeDKTModel real, dims minúsculas — n_problems(M)=3, input_dim=2M (code_dkt.py:148,150),
    # embeddings/hidden pequenos p/ rodar instantâneo na CPU. Pesos de seed fixa, não treinados.
    seed_all_random_generators(42, strict=False)
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

    # DATA_ROOT aponta para tmp_path (data_root), e a turma "Turma 6" vira o slug "turma-6".
    store = TrainedModelFileStore(conn)
    artifact_id = store.save(
        TrainingDataset(
            events=pd.DataFrame(),
            classroom_slug=ClassroomSlug.from_name("Turma 6"),
            progsnap_assignment_id=ProgSnapAssignmentId(439),
            classroom_id=classroom_id,
        ),
        assignment_id,
        TrainingOutcome(
            model=model, vocab=tiny_vocab, hyperparameters=tiny_config,
            first_attempt_auc=None, java_parse_rate=1.0,
        ),
    )
    trained_model = SqliteTrainedModelRepository(conn).get(artifact_id)
    # Publica a versão: é por aqui que o dashboard a encontra.
    SqliteAssignmentRepository(conn).set_published_model(assignment_id, artifact_id)

    # Q-matrix determinística: problemas 1,2,3 → KC1/KC2; o problema 3 liga AMBOS os KCs,
    # forçando a média problem→KC (Pitfall 2: KC-mastery = mean sobre os problemas do KC).
    from api.knowledge_components.domain.entities.knowledge_component_entity import (
        KnowledgeComponent,
    )
    from api.knowledge_components.domain.entities.qmatrix_binding_entity import QMatrixBinding
    from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
        SqliteKnowledgeComponentRepository,
    )
    from api.knowledge_components.infrastructure.repositories.sqlite_qmatrix_repository import (
        SqliteQMatrixRepository,
    )

    kc_repo = SqliteKnowledgeComponentRepository(conn)
    kc1 = kc_repo.add(
        KnowledgeComponent(id=None, assignment_id=assignment_id, name="Laços", group_index=0)
    )
    kc2 = kc_repo.add(
        KnowledgeComponent(id=None, assignment_id=assignment_id, name="Condicionais", group_index=1)
    )
    qm_repo = SqliteQMatrixRepository(conn)
    bindings = [(kc1, 1), (kc1, 3), (kc2, 2), (kc2, 3)]
    for kc_id, problem_id in bindings:
        qm_repo.add(
            QMatrixBinding(id=None, assignment_id=assignment_id, kc_id=kc_id, problem_id=problem_id)
        )

    kcs = kc_repo.list_by_assignment(assignment_id)
    qmatrix = qm_repo.list_by_assignment(assignment_id)

    class _TrainedArtifact:
        pass

    ns = _TrainedArtifact()
    ns.conn = conn
    ns.classroom_id = classroom_id
    ns.assignment_id = assignment_id
    ns.artifact_id = artifact_id
    ns.version_number = trained_model.version_number
    ns.artifact_dir = trained_model.model_dir
    ns.trained_model = trained_model
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
    return Path(__file__).resolve().parent / "tests" / "data" / "kc"


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
