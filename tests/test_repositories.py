"""Round-trip das 8 entidades de domínio + repositórios parametrizados (MODEL-04 / SC4).

SC4: cada entidade faz insert → get → dataclass igual ao gravado, referenciando artefatos
do FS por CAMINHO (nunca o blob). As asserções pinam invariantes (round-trip fiel, FK
aplicada, SQL parametrizado), não valores mágicos — espelha test_sequences.py. Herméticos,
CPU-only, sobre a fixture tmp_db de 02-01 (schema em user_version=1).
"""

from __future__ import annotations

import sqlite3

import pytest

from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos


def _seed_turma_assignment(conn) -> tuple[int, int]:
    """Insere uma turma + assignment e devolve (turma_id, assignment_id).

    A maioria das entidades pendura numa assignment válida (FK), então este helper monta
    o mínimo de pai antes dos round-trips filhos."""
    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name="Turma A", created_at="2026-06-21T00:00:00Z")
    )
    assignment_id = repos.AssignmentRepository(conn).insert(
        models.Assignment(
            id=None,
            turma_id=turma_id,
            name="A1",
            current_version_id=None,
            created_at="2026-06-21T00:00:00Z",
        )
    )
    return turma_id, assignment_id


def test_eight_entities_roundtrip(tmp_db):
    conn = tmp_db
    turma_id, assignment_id = _seed_turma_assignment(conn)

    # Turma + Assignment já inseridas no helper: lê de volta e compara.
    turma = repos.TurmaRepository(conn).get(turma_id)
    assert turma == models.Turma(id=turma_id, name="Turma A", created_at="2026-06-21T00:00:00Z")

    assignment = repos.AssignmentRepository(conn).get(assignment_id)
    assert assignment == models.Assignment(
        id=assignment_id,
        turma_id=turma_id,
        name="A1",
        current_version_id=None,
        created_at="2026-06-21T00:00:00Z",
    )

    submission = models.Submission(
        id=None,
        assignment_id=assignment_id,
        code_state_id="cs1",
        subject_id="S1",
        problem_id=1,
        score=1.0,
        created_at="2026-06-21T00:00:00Z",
    )
    sub_id = repos.SubmissionRepository(conn).insert(submission)
    # Sem get(): a produção só insere submissões; o round-trip é conferido direto na tabela.
    row = conn.execute(
        "SELECT assignment_id, code_snapshot_id, student_id, problem_id, score, created_at "
        "FROM submission WHERE id = ?;",
        (sub_id,),
    ).fetchone()
    assert tuple(row) == (assignment_id, "cs1", "S1", 1, 1.0, "2026-06-21T00:00:00Z")

    kc = models.KC(id=None, assignment_id=assignment_id, name="laços")
    kc_id = repos.KCRepository(conn).insert(kc)
    assert repos.KCRepository(conn).get(kc_id) == models.KC(
        id=kc_id, assignment_id=assignment_id, name="laços"
    )

    qm = models.QMatrix(id=None, assignment_id=assignment_id, kc_id=kc_id, problem_id=1)
    qm_id = repos.QMatrixRepository(conn).insert(qm)
    assert repos.QMatrixRepository(conn).list_by_assignment(assignment_id) == [
        models.QMatrix(id=qm_id, assignment_id=assignment_id, kc_id=kc_id, problem_id=1)
    ]

    artifact = models.ModelArtifact(
        id=None,
        assignment_id=assignment_id,
        version_number=1,
        content_hash="deadbeef",
        artifact_dir="data/1/versions/1",
        created_at="2026-06-21T00:00:00Z",
    )
    art_id = repos.ModelArtifactRepository(conn).insert(artifact)
    assert repos.ModelArtifactRepository(conn).get(art_id) == models.ModelArtifact(
        id=art_id,
        assignment_id=assignment_id,
        version_number=1,
        content_hash="deadbeef",
        artifact_dir="data/1/versions/1",
        created_at="2026-06-21T00:00:00Z",
    )

    mastery = models.MasteryPrediction(
        id=None, model_artifact_id=art_id, subject_id="S1", kc_id=kc_id, mastery=0.75
    )
    m_id = repos.MasteryPredictionRepository(conn).insert(mastery)
    assert repos.MasteryPredictionRepository(conn).list_by_artifact(art_id) == [
        models.MasteryPrediction(
            id=m_id, model_artifact_id=art_id, subject_id="S1", kc_id=kc_id, mastery=0.75
        )
    ]

    job = models.TrainingJob(
        id=None, assignment_id=assignment_id, status="pending", created_at="2026-06-21T00:00:00Z"
    )
    job_id = repos.TrainingJobRepository(conn).insert(job)
    assert repos.TrainingJobRepository(conn).get(job_id) == models.TrainingJob(
        id=job_id, assignment_id=assignment_id, status="pending", created_at="2026-06-21T00:00:00Z"
    )


def test_model_artifact_references_fs_by_path(tmp_db):
    # ModelArtifact persiste o CAMINHO do diretório de artefato; nenhuma coluna guarda bytes.
    conn = tmp_db
    _, assignment_id = _seed_turma_assignment(conn)
    art_id = repos.ModelArtifactRepository(conn).insert(
        models.ModelArtifact(
            id=None,
            assignment_id=assignment_id,
            version_number=1,
            content_hash=None,
            artifact_dir="data/1/versions/1",
            created_at="2026-06-21T00:00:00Z",
        )
    )
    loaded = repos.ModelArtifactRepository(conn).get(art_id)
    assert isinstance(loaded.artifact_dir, str)
    assert loaded.artifact_dir == "data/1/versions/1"

    # Nenhuma coluna da tabela carrega bytes/blob (todas TEXT/INTEGER/REAL).
    types = {row["name"]: row["type"] for row in conn.execute("PRAGMA table_info(model_artifact);")}
    assert all(t.upper() != "BLOB" for t in types.values())


def test_fk_enforced(tmp_db):
    # foreign_keys=ON (herdado de 02-01): Submission com assignment_id órfão -> IntegrityError.
    conn = tmp_db
    orphan = models.Submission(
        id=None,
        assignment_id=999999,
        code_state_id="cs",
        subject_id="S1",
        problem_id=1,
        score=0.0,
        created_at="2026-06-21T00:00:00Z",
    )
    with pytest.raises(sqlite3.IntegrityError):
        repos.SubmissionRepository(conn).insert(orphan)


def test_assignment_status_roundtrip(tmp_db):
    # status é estado de primeira classe (D-05/D-08): 'eda_only' | 'trainable' fazem
    # round-trip fiel pelo insert→get (a ingestão sempre grava explícito).
    conn = tmp_db
    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name="Turma A", created_at="2026-06-21T00:00:00Z")
    )
    for status in ("statistics_only", "ready_for_kc_generation"):
        aid = repos.AssignmentRepository(conn).insert(
            models.Assignment(
                id=None,
                turma_id=turma_id,
                name=f"A-{status}",
                current_version_id=None,
                created_at="2026-06-21T00:00:00Z",
                status=status,
            )
        )
        assert repos.AssignmentRepository(conn).get(aid).status == status


def test_submission_event_type_roundtrip(tmp_db):
    # event_type vem do filtro do stream canônico (D-10/D-13): Run.Program | Compile.Error.
    conn = tmp_db
    _, assignment_id = _seed_turma_assignment(conn)
    sub = models.Submission(
        id=None,
        assignment_id=assignment_id,
        code_state_id="cs1",
        subject_id="S1",
        problem_id=1,
        score=1.0,
        created_at="2026-06-21T00:00:00Z",
        event_type="Run.Program",
    )
    sub_id = repos.SubmissionRepository(conn).insert(sub)
    row = conn.execute("SELECT event_type FROM submission WHERE id = ?;", (sub_id,)).fetchone()
    assert row["event_type"] == "Run.Program"


def test_kc_index_roundtrip(tmp_db):
    # kc_index (id de cluster 0..N por-assignment, degrau 0005) faz round-trip fiel — é o
    # "kc_id científico" do TCC que o replay de referência compara, distinto do kc.id autoincrement global.
    conn = tmp_db
    _, assignment_id = _seed_turma_assignment(conn)
    kc_id = repos.KCRepository(conn).insert(
        models.KC(id=None, assignment_id=assignment_id, name="laços", kc_index=7)
    )
    loaded = repos.KCRepository(conn).get(kc_id)
    assert loaded == models.KC(
        id=kc_id, assignment_id=assignment_id, name="laços", kc_index=7
    )


def test_kc_index_born_null(tmp_db):
    # KC criado sem kc_index (ex.: professor adiciona um KC à mão, KC-02) nasce com kc_index None.
    conn = tmp_db
    _, assignment_id = _seed_turma_assignment(conn)
    kc_id = repos.KCRepository(conn).insert(
        models.KC(id=None, assignment_id=assignment_id, name="manual")
    )
    assert repos.KCRepository(conn).get(kc_id).kc_index is None


def test_kc_job_roundtrip_and_transitions(tmp_db):
    # KCJob espelha TrainingJob: insert → get → mark_running → update_stage → mark_done, com
    # os valores sobrevivendo a cada transição (estado do pipeline lido por polling GET, D-05).
    conn = tmp_db
    _, assignment_id = _seed_turma_assignment(conn)
    repo = repos.KCJobRepository(conn)
    job_id = repo.insert(
        models.KCJob(
            id=None, assignment_id=assignment_id, status="pending", created_at="2026-06-21T00:00:00Z"
        )
    )

    # Nasce pending com os campos de progresso None.
    job = repo.get(job_id)
    assert job == models.KCJob(
        id=job_id, assignment_id=assignment_id, status="pending", created_at="2026-06-21T00:00:00Z"
    )
    assert job.stage is None and job.started_at is None and job.error_message is None

    repo.mark_running(job_id, started_at="2026-06-21T00:00:01Z")
    job = repo.get(job_id)
    assert job.status == "running"
    assert job.started_at == "2026-06-21T00:00:01Z"

    repo.update_stage(job_id, stage="cluster", updated_at="2026-06-21T00:00:05Z")
    job = repo.get(job_id)
    assert job.stage == "cluster"
    assert job.updated_at == "2026-06-21T00:00:05Z"

    repo.mark_done(job_id, updated_at="2026-06-21T00:00:10Z")
    job = repo.get(job_id)
    assert job.status == "done"
    assert job.updated_at == "2026-06-21T00:00:10Z"


def test_kc_job_mark_failed(tmp_db):
    # Falha-dura do pipeline (D-04): marca o job failed com a mensagem clara, NADA persistido.
    conn = tmp_db
    _, assignment_id = _seed_turma_assignment(conn)
    repo = repos.KCJobRepository(conn)
    job_id = repo.insert(
        models.KCJob(
            id=None, assignment_id=assignment_id, status="pending", created_at="2026-06-21T00:00:00Z"
        )
    )
    repo.mark_failed(job_id, "0 KCs gerados para o problema 3")
    job = repo.get(job_id)
    assert job.status == "failed"
    assert "0 KCs" in job.error_message


def test_sql_is_parametrized(tmp_db):
    # Valor malicioso é gravado como dado literal, não executado (placeholders ?).
    conn = tmp_db
    evil = "x'); DROP TABLE turma; --"
    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name=evil, created_at="2026-06-21T00:00:00Z")
    )
    # A tabela continua existindo e o nome foi gravado verbatim.
    assert repos.TurmaRepository(conn).get(turma_id).name == evil
    conn.execute("SELECT 1 FROM classroom LIMIT 1;")  # não levanta: tabela não foi dropada
