# Rotas de /knowledge-components, disparo/progresso da geração, edição e aprovação dos KCs.
from __future__ import annotations

import subprocess
import sys

from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.entities.problem_knowledge_component_entity import (
    ProblemKnowledgeComponent,
)
from api.knowledge_components.infrastructure.repositories.sqlite_kc_generation_job_repository import (
    SqliteKnowledgeComponentGenerationJobRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_problem_knowledge_component_repository import (
    SqliteProblemKnowledgeComponentRepository,
)
from api.knowledge_components.presentation.dependencies import KC_GENERATION_WORKER
from tests.fixtures.assignments import add_assignment
from tests.fixtures.classrooms import add_classroom
from tests.fixtures.problems import add_problems

_NOW = "2026-06-21T00:00:00Z"


def _seed_kc(conn, assignment_id, name, kc_index=None, generated_name=None) -> int:
    return SqliteKnowledgeComponentRepository(conn).add(
        KnowledgeComponent(
            id=None,
            assignment_id=assignment_id,
            name=name,
            group_index=kc_index,
            generated_name=generated_name,
        )
    )


def _bind(conn, assignment_id, kc_id, problem_id) -> None:
    add_problems(conn, assignment_id, [problem_id])
    SqliteProblemKnowledgeComponentRepository(conn).add(
        ProblemKnowledgeComponent(id=None, assignment_id=assignment_id, kc_id=kc_id, problem_id=problem_id)
    )


def _updated_at(conn, kc_id) -> str | None:
    return conn.execute("SELECT updated_at FROM kc WHERE id = ?;", (kc_id,)).fetchone()[0]


def _markers(client, assignment_id) -> dict[str, bool]:
    # O marcador de gerado de cada conceito, como a rota da tela Conceitos o entrega
    body = client.get(f"/assignments/{assignment_id}/problems/knowledge-components").json()
    return {
        kc["name"]: kc["is_generated_by_llm"]
        for problem in body["problems"]
        for kc in problem["knowledge_components"]
    }


# Captura os args do dispatch sem spawnar processo, KC-gen real nunca roda.
class _FakePopen:
    calls: list[list[str]] = []

    def __init__(self, args, *a, **kw):
        type(self).calls.append(args)


# --- dispatch e poll ----------------------------------


def test_generate_dispatches_list_form_and_returns_job_id(api_client, monkeypatch):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="ready_for_kc_generation")
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)

    resp = client.post("/knowledge-components/generation-jobs", json={"assignment_id": aid})

    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert isinstance(job_id, int)
    assert len(_FakePopen.calls) == 1
    args = _FakePopen.calls[0]
    assert args == [
        sys.executable,
        "-m",
        KC_GENERATION_WORKER,
        "--assignment",
        str(aid),
        "--job-id",
        str(job_id),
    ]
    assert all(isinstance(a, str) for a in args)  # sem shell / sem interpolação


def test_poll_returns_job_fields(api_client, monkeypatch):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="ready_for_kc_generation")
    _FakePopen.calls = []
    monkeypatch.setattr(subprocess, "Popen", _FakePopen)
    job_id = client.post("/knowledge-components/generation-jobs", json={"assignment_id": aid}).json()["job_id"]

    # Simula o subprocess marcando running + estágio sob WAL (conexão de teste separada).
    job_repo = SqliteKnowledgeComponentGenerationJobRepository(conn)
    job_repo.mark_running(job_id, started_at=_NOW)
    job_repo.update_stage(job_id, stage="cluster", updated_at=_NOW)

    resp = client.get(f"/knowledge-components/generation-jobs/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["status"] == "running"
    assert body["stage"] == "cluster"


def test_poll_missing_job_404(api_client):
    client, _ = api_client
    assert client.get("/knowledge-components/generation-jobs/9999").status_code == 404


# Edição dos KCs


def test_renaming_a_generated_concept_records_the_edit_and_drops_the_marker(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    kc_id = _seed_kc(conn, aid, "nome antigo", generated_name="old name")
    _bind(conn, aid, kc_id, problem_id=1)
    assert _markers(client, aid) == {"nome antigo": True}

    resp = client.put(f"/knowledge-components/{kc_id}", json={"name": "nome novo"})

    assert resp.status_code == 200
    assert resp.json() == {"id": kc_id, "name": "nome novo", "is_generated_by_llm": False}
    assert SqliteKnowledgeComponentRepository(conn).get(kc_id).name == "nome novo"
    assert _updated_at(conn, kc_id) is not None
    assert _markers(client, aid) == {"nome novo": False}


def test_renaming_to_the_same_name_writes_nothing(api_client):
    # O mesmo nome não é edição, então não tira as estrelas nem reabre a aprovação
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_approved")
    kc_id = _seed_kc(conn, aid, "Laços", generated_name="loops")
    _bind(conn, aid, kc_id, problem_id=1)

    resp = client.put(f"/knowledge-components/{kc_id}", json={"name": "Laços"})

    assert resp.status_code == 200
    assert resp.json() == {"id": kc_id, "name": "Laços", "is_generated_by_llm": True}
    assert _updated_at(conn, kc_id) is None
    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_approved"


def test_renaming_to_the_same_name_after_training_is_still_refused(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="trained")
    kc_id = _seed_kc(conn, aid, "Laços", generated_name="loops")
    _bind(conn, aid, kc_id, problem_id=1)

    resp = client.put(f"/knowledge-components/{kc_id}", json={"name": "Laços"})

    assert resp.status_code == 409
    assert resp.json()["detail"] == "os conceitos de um exercício treinado não mudam"


def test_the_screen_route_marks_only_the_generated_concepts_nobody_renamed(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    generated = _seed_kc(conn, aid, "Laços", generated_name="loops")
    renamed = _seed_kc(conn, aid, "Condicionais", generated_name="conditionals")
    for kc_id in (generated, renamed):
        _bind(conn, aid, kc_id, problem_id=1)
    renamed_response = client.put(f"/knowledge-components/{renamed}", json={"name": "Desvios"})
    assert renamed_response.status_code == 200
    created = client.post(
        "/knowledge-components", json={"assignment_id": aid, "name": "Vetores", "problem_ids": [1]}
    )
    assert created.status_code == 201

    assert _markers(client, aid) == {"Laços": True, "Desvios": False, "Vetores": False}


def test_remove_that_empties_a_problem_is_blocked(api_client):
    # remover o único KC de um problema o deixaria com 0 KCs → BLOQUEADO + ROLLBACK.
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    only_kc = _seed_kc(conn, aid, "único")
    _bind(conn, aid, only_kc, problem_id=1)

    resp = client.delete(f"/knowledge-components/{only_kc}")
    assert resp.status_code >= 400  # rejeitado

    # ROLLBACK, o KC e seu binding continuam intactos.
    assert SqliteKnowledgeComponentRepository(conn).get(only_kc) is not None
    assert conn.execute("SELECT COUNT(*) FROM problem_kc WHERE kc_id=?;", (only_kc,)).fetchone()[0] == 1


# --- aprovação dos KCs pelo professor ---


def test_approve_sets_kc_approved(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    kc_id = _seed_kc(conn, aid, "x")
    _bind(conn, aid, kc_id, problem_id=1)

    resp = client.post("/knowledge-components/approve", json={"assignment_id": aid})
    assert resp.status_code == 200

    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_approved"


def test_approve_rejects_non_draft_assignment(api_client):
    # Aprovar sem gerar KCs burlaria a revisão e treinaria sobre KCs inexistentes, é 409.
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="ready_for_kc_generation")

    resp = client.post("/knowledge-components/approve", json={"assignment_id": aid})
    assert resp.status_code == 409
    assert SqliteAssignmentRepository(conn).get(aid).status == "ready_for_kc_generation"  # parado


def test_approve_rejects_draft_without_kcs(api_client):
    # kc_draft mas SEM nenhum KC não pode ser aprovado (não há KC a treinar).
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")  # nenhum KC inserido

    resp = client.post("/knowledge-components/approve", json={"assignment_id": aid})
    assert resp.status_code == 409
    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_draft"


def test_approve_rejects_a_problem_without_a_concept_and_names_it(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    kc_id = _seed_kc(conn, aid, "Laços")
    _bind(conn, aid, kc_id, problem_id=1)
    add_problems(conn, aid, [2, 3])

    resp = client.post("/knowledge-components/approve", json={"assignment_id": aid})

    assert resp.status_code == 409
    assert resp.json()["detail"] == "problemas sem nenhum KC [2, 3]"
    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_draft"


def test_approve_of_a_draft_with_problems_and_no_concept_gives_only_the_empty_draft_refusal(
    api_client,
):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    add_problems(conn, aid, [1, 2])

    resp = client.post("/knowledge-components/approve", json={"assignment_id": aid})

    assert resp.status_code == 409
    assert resp.json()["detail"] == "assignment não tem nenhum KC para aprovar"


def test_editing_after_approval_reverts_status(api_client):
    # editar um KC após aprovar reverte kc_approved → kc_draft (re-aprovação necessária).
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_approved")
    a = _seed_kc(conn, aid, "a")
    b = _seed_kc(conn, aid, "b")
    _bind(conn, aid, a, problem_id=1)
    _bind(conn, aid, b, problem_id=1)  # problema 1 tem 2 KCs (remover 1 não o zera)

    resp = client.put(f"/knowledge-components/{a}", json={"name": "a-editado"})
    assert resp.status_code == 200

    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_draft"


def test_editing_after_training_is_refused(api_client):
    # sem re-treino, o modelo publicado fixa os conceitos; qualquer edição é 409 e nada muda.
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="trained")
    a = _seed_kc(conn, aid, "a")
    b = _seed_kc(conn, aid, "b")
    _bind(conn, aid, a, problem_id=1)
    _bind(conn, aid, b, problem_id=1)

    renamed = client.put(f"/knowledge-components/{a}", json={"name": "a-editado"})
    removed = client.delete(f"/knowledge-components/{a}")

    assert renamed.status_code == 409 and removed.status_code == 409
    assert SqliteKnowledgeComponentRepository(conn).get(a).name == "a"
    assert SqliteAssignmentRepository(conn).get(aid).status == "trained"


# Tirar um KC de um problema só, no botão remover do chip, e o caminho de volta


def _active_links(conn, kc_id) -> list[int]:
    rows = conn.execute(
        "SELECT problem_id FROM problem_kc WHERE kc_id = ? AND deleted_at IS NULL ORDER BY 1;",
        (kc_id,),
    ).fetchall()
    return [r[0] for r in rows]


def test_removing_a_kc_from_one_problem_keeps_it_on_the_others(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    loops, other = _seed_kc(conn, aid, "laços"), _seed_kc(conn, aid, "outro")
    for problem_id in (1, 2):
        _bind(conn, aid, loops, problem_id)
        _bind(conn, aid, other, problem_id)

    resp = client.delete(f"/knowledge-components/{loops}/problems/1")

    assert resp.status_code == 200
    assert resp.json() == {"kc_id": loops, "problem_id": 1, "knowledge_component_removed": False}
    assert _active_links(conn, loops) == [2]
    # Soft delete, o vínculo removido continua na tabela com a data
    removed = conn.execute(
        "SELECT deleted_at FROM problem_kc WHERE kc_id = ? AND problem_id = 1;", (loops,)
    ).fetchone()[0]
    assert removed is not None


def test_removing_the_only_kc_of_a_problem_is_refused_and_nothing_changes(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    only = _seed_kc(conn, aid, "único")
    _bind(conn, aid, only, problem_id=1)

    resp = client.delete(f"/knowledge-components/{only}/problems/1")

    assert resp.status_code == 409
    assert _active_links(conn, only) == [1]
    assert SqliteKnowledgeComponentRepository(conn).get(only) is not None


def test_a_kc_that_loses_its_last_problem_is_removed_too(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    leaving, staying = _seed_kc(conn, aid, "sai"), _seed_kc(conn, aid, "fica")
    _bind(conn, aid, leaving, problem_id=1)
    _bind(conn, aid, staying, problem_id=1)

    resp = client.delete(f"/knowledge-components/{leaving}/problems/1")

    assert resp.json()["knowledge_component_removed"] is True
    assert SqliteKnowledgeComponentRepository(conn).get(leaving) is None
    kc_row = conn.execute("SELECT deleted_at FROM kc WHERE id = ?;", (leaving,)).fetchone()
    assert kc_row[0] is not None  # o KC também fica como histórico


def test_removing_a_link_sends_approved_kcs_back_to_draft(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_approved")
    loops, other = _seed_kc(conn, aid, "laços"), _seed_kc(conn, aid, "outro")
    _bind(conn, aid, loops, problem_id=1)
    _bind(conn, aid, other, problem_id=1)

    client.delete(f"/knowledge-components/{loops}/problems/1")

    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_draft"


def test_removing_a_missing_kc_or_link_is_404(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    kc_id = _seed_kc(conn, aid, "k")
    _bind(conn, aid, kc_id, problem_id=1)

    assert client.delete("/knowledge-components/999/problems/1").status_code == 404
    assert client.delete(f"/knowledge-components/{kc_id}/problems/7").status_code == 404


def test_linking_an_existing_kc_to_another_problem_creates_a_new_row(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_approved")
    loops, other = _seed_kc(conn, aid, "laços"), _seed_kc(conn, aid, "outro")
    _bind(conn, aid, loops, problem_id=1)
    _bind(conn, aid, loops, problem_id=2)
    _bind(conn, aid, other, problem_id=2)
    client.delete(f"/knowledge-components/{loops}/problems/2")

    resp = client.post(f"/knowledge-components/{loops}/problems/2")

    assert resp.status_code == 201
    assert resp.json() == {"kc_id": loops, "problem_id": 2}
    assert _active_links(conn, loops) == [1, 2]
    total = conn.execute(
        "SELECT COUNT(*) FROM problem_kc WHERE kc_id = ? AND problem_id = 2;", (loops,)
    ).fetchone()[0]
    assert total == 2  # a linha removida fica como histórico e nasce outra
    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_draft"


def test_linking_is_refused_for_a_repeated_link_or_a_problem_of_another_assignment(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    kc_id = _seed_kc(conn, aid, "k")
    _bind(conn, aid, kc_id, problem_id=1)

    repeated = client.post(f"/knowledge-components/{kc_id}/problems/1")
    unknown = client.post(f"/knowledge-components/{kc_id}/problems/99")

    assert repeated.status_code == 409
    assert unknown.status_code == 409
    assert client.post("/knowledge-components/999/problems/1").status_code == 404


def test_a_kc_of_a_removed_assignment_is_404_on_every_route_by_kc_id(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    kc_id = _seed_kc(conn, aid, "k")
    _bind(conn, aid, kc_id, problem_id=1)
    conn.execute("UPDATE assignment SET deleted_at = 't1' WHERE id = ?;", (aid,))

    assert client.put(f"/knowledge-components/{kc_id}", json={"name": "x"}).status_code == 404
    assert client.delete(f"/knowledge-components/{kc_id}").status_code == 404
    assert client.post(f"/knowledge-components/{kc_id}/problems/1").status_code == 404
    assert client.delete(f"/knowledge-components/{kc_id}/problems/1").status_code == 404


# Criar um conceito, sempre ligado a ao menos um problema


def _create(client, assignment_id, problem_ids):
    return client.post(
        "/knowledge-components",
        json={"assignment_id": assignment_id, "name": "Vetores", "problem_ids": problem_ids},
    )


def test_creating_a_concept_binds_it_to_the_chosen_problems(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    add_problems(conn, aid, [1, 2, 3])

    resp = _create(client, aid, [1, 3])

    assert resp.status_code == 201
    kc_id = resp.json()["id"]
    assert resp.json() == {"id": kc_id, "name": "Vetores", "is_generated_by_llm": False}
    assert _active_links(conn, kc_id) == [1, 3]
    created = SqliteKnowledgeComponentRepository(conn).get(kc_id)
    # O conceito do professor nasce sem grupo, sem nome gerado e sem edição
    assert (created.group_index, created.generated_name, created.updated_at) == (None, None, None)


def test_creating_a_concept_needs_at_least_one_problem(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_draft")
    add_problems(conn, aid, [1])

    empty = _create(client, aid, [])
    missing = client.post("/knowledge-components", json={"assignment_id": aid, "name": "Vetores"})

    assert (empty.status_code, missing.status_code) == (422, 422)
    assert SqliteKnowledgeComponentRepository(conn).list_by_assignment(aid) == []


def test_creating_a_concept_sends_approved_concepts_back_to_draft(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="kc_approved")
    add_problems(conn, aid, [1])

    assert _create(client, aid, [1]).status_code == 201

    assert SqliteAssignmentRepository(conn).get(aid).status == "kc_draft"


def test_creating_a_concept_after_training_is_refused_and_nothing_changes(api_client):
    client, conn = api_client
    aid = add_assignment(conn, add_classroom(conn), status="trained")
    add_problems(conn, aid, [1])

    resp = _create(client, aid, [1])

    assert resp.status_code == 409
    assert SqliteKnowledgeComponentRepository(conn).list_by_assignment(aid) == []
    assert SqliteAssignmentRepository(conn).get(aid).status == "trained"


def test_creating_a_concept_with_a_problem_of_another_assignment_is_refused(api_client):
    client, conn = api_client
    classroom_id = add_classroom(conn)
    aid = add_assignment(conn, classroom_id, status="kc_draft")
    other = add_assignment(conn, classroom_id, name="B", status="kc_draft")
    add_problems(conn, aid, [1])
    add_problems(conn, other, [9])

    resp = _create(client, aid, [1, 9])

    assert resp.status_code == 409
    assert resp.json()["detail"] == "problemas que não existem no assignment [9]"
    assert SqliteKnowledgeComponentRepository(conn).list_by_assignment(aid) == []
