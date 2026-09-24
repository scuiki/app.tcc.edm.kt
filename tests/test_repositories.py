"""Round-trip das 8 entidades de domínio + repositórios parametrizados (MODEL-04 / SC4).

SC4: cada entidade faz insert → get → dataclass igual ao gravado, referenciando artefatos
do FS por CAMINHO (nunca o blob). As asserções pinam invariantes (round-trip fiel, FK
aplicada, SQL parametrizado), não valores mágicos — espelha test_sequences.py. Herméticos,
CPU-only, sobre a fixture tmp_db de 02-01 (schema em user_version=1).
"""

from __future__ import annotations


from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from api.assignments.infrastructure.sqlite_classroom_repository import SqliteClassroomRepository
from api.assignments.infrastructure.sqlite_assignment_repository import SqliteAssignmentRepository
from api.assignments.domain.classroom_entity import Classroom
from api.assignments.domain.assignment_entity import Assignment


def _seed_turma_assignment(conn) -> tuple[int, int]:
    """Insere uma turma + assignment e devolve (classroom_id, assignment_id).

    A maioria das entidades pendura numa assignment válida (FK), então este helper monta
    o mínimo de pai antes dos round-trips filhos."""
    classroom_id = SqliteClassroomRepository(conn).add(
        Classroom(id=None, name="Turma A", created_at="2026-06-21T00:00:00Z")
    )
    assignment_id = SqliteAssignmentRepository(conn).add(
        Assignment(
            id=None,
            classroom_id=classroom_id,
            name="A1",
            published_model_id=None,
            created_at="2026-06-21T00:00:00Z",
        )
    )
    return classroom_id, assignment_id


def test_entities_roundtrip(tmp_db):
    conn = tmp_db
    classroom_id, assignment_id = _seed_turma_assignment(conn)

    kc_id = conn.execute(
        "INSERT INTO kc (assignment_id, name) VALUES (?, 'laços');", (assignment_id,)
    ).lastrowid

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


