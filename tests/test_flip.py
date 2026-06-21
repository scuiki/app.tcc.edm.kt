"""Flip atômico do ponteiro current_version_id (MODEL-04 / D-06 / Pitfall 2).

O ponteiro "current" de um Assignment é trocado por um único UPDATE transacional; o
diretório do artefato nunca é tocado pelo flip (o ponteiro no DB é a fonte única — D-06), e
a ordem load-bearing (blob write-once → INSERT ModelArtifact → flip) garante que um leitor
que pegue o ponteiro antigo leia uma versão completa e válida (Pitfall 2). Herméticos,
CPU-only, sobre tmp_db de 02-01.
"""

from __future__ import annotations

from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.artifacts import ArtifactStore, flip_current


def _seed_turma_assignment(conn) -> int:
    """Insere turma + assignment e devolve o assignment_id (current_version_id nasce NULL)."""
    turma_id = repos.TurmaRepository(conn).insert(
        models.Turma(id=None, name="Turma A", created_at="2026-06-21T00:00:00Z")
    )
    return repos.AssignmentRepository(conn).insert(
        models.Assignment(
            id=None,
            turma_id=turma_id,
            name="A1",
            current_version_id=None,
            created_at="2026-06-21T00:00:00Z",
        )
    )


def test_flip_atomic_pointer(tmp_db):
    # Após inserir um ModelArtifact, flip_current atualiza Assignment.current_version_id num
    # UPDATE transacional; antes do flip o ponteiro é NULL, depois aponta para a nova versão.
    conn = tmp_db
    assignment_id = _seed_turma_assignment(conn)

    art_id = repos.ModelArtifactRepository(conn).insert(
        models.ModelArtifact(
            id=None,
            assignment_id=assignment_id,
            version_number=1,
            content_hash="deadbeef",
            artifact_dir="data/1/1/models/v1",
            created_at="2026-06-21T00:00:00Z",
        )
    )

    # antes do flip: o ponteiro current ainda é NULL (nasce assim — D-06).
    before = repos.AssignmentRepository(conn).get(assignment_id)
    assert before.current_version_id is None

    flip_current(conn, assignment_id, art_id)

    after = repos.AssignmentRepository(conn).get(assignment_id)
    assert after.current_version_id == art_id


def test_flip_does_not_touch_artifact_dir(tmp_db, tmp_path, tiny_model, tiny_vocab, tiny_config):
    # O flip mexe SÓ no ponteiro do DB; o diretório do artefato (write-once) fica intacto.
    conn = tmp_db
    assignment_id = _seed_turma_assignment(conn)
    store = ArtifactStore(str(tmp_path / "data"))

    persisted = store.persist(conn, 1, assignment_id, tiny_model, tiny_vocab, tiny_config)
    import pathlib

    vdir = pathlib.Path(persisted["dir"])
    blob_before = (vdir / "model.pt").read_bytes()

    flip_current(conn, assignment_id, persisted["artifact_id"])

    # o flip não reescreveu nem removeu o blob.
    assert (vdir / "model.pt").read_bytes() == blob_before
    assert repos.AssignmentRepository(conn).get(assignment_id).current_version_id == persisted[
        "artifact_id"
    ]


def test_flip_is_last_step_order(tmp_db, tmp_path, tiny_model, tiny_vocab, tiny_config):
    # Ordem load-bearing (Pitfall 2): persist grava o blob E insere a linha ANTES de qualquer
    # flip. Antes de chamar flip_current, o ponteiro ainda não enxerga a nova versão.
    conn = tmp_db
    assignment_id = _seed_turma_assignment(conn)
    store = ArtifactStore(str(tmp_path / "data"))

    persisted = store.persist(conn, 1, assignment_id, tiny_model, tiny_vocab, tiny_config)
    # blob completo + linha inserida, mas SEM flip ainda -> ponteiro continua NULL.
    assert repos.AssignmentRepository(conn).get(assignment_id).current_version_id is None
    import pathlib

    assert (pathlib.Path(persisted["dir"]) / "model.pt").exists()

    flip_current(conn, assignment_id, persisted["artifact_id"])
    assert (
        repos.AssignmentRepository(conn).get(assignment_id).current_version_id
        == persisted["artifact_id"]
    )
