"""Value objects da app layer — invariantes que hoje vivem espalhadas como checagens soltas.

Cada VO carrega UMA invariante que o código repetia em vários lugares: o componente de caminho
derivado de um nome do professor (`_slug`, 7 definições), o CodeStateID que vira nome de arquivo
(`_safe_csid_name`), o caminho confinado sob uma raiz (`_confine`, mais dois espelhos no
ArtifactStore) e o AssignmentID do ProgSnap2 (`_progsnap_aid`, 5 definições).

O `ProgSnapAssignmentId` existe por um motivo concreto e documentado: o repo tem DOIS id-spaces
inteiros distintos — o id do banco (autoincrement) e o AssignmentID do ProgSnap2 — e confundi-los
já custou uma consulta manual ao app.db durante a UAT da Fase 4 (backlog 999.2). Um int não
distingue os dois; um tipo sim.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from edmkt_app import values


# --- TurmaSlug: nome arbitrário do professor -> componente de caminho seguro ----------------


def test_turma_slug_normalizes():
    assert str(values.TurmaSlug.from_name("Turma 6")) == "turma-6"
    assert str(values.TurmaSlug.from_name("CSEDM Spring 2019")) == "csedm-spring-2019"


def test_turma_slug_collapses_unsafe_characters():
    # O nome vem do professor: qualquer coisa fora de [a-z0-9] colapsa em "-", então nenhum
    # separador de caminho, "..", ou byte exótico sobrevive para virar diretório.
    slug = str(values.TurmaSlug.from_name("../etc/passwd"))
    assert "/" not in slug and ".." not in slug


def test_turma_slug_falls_back_when_nothing_survives():
    assert str(values.TurmaSlug.from_name("   ")) == "turma"
    assert str(values.TurmaSlug.from_name("!!!")) == "turma"


def test_turma_slug_is_idempotent():
    # features_cache.py:66 fazia _slug(turma_slug) — slug de um valor já slugificado. Idempotência
    # torna esse tipo de aplicação dupla inofensiva em vez de silenciosamente errada.
    once = values.TurmaSlug.from_name("Turma 6")
    twice = values.TurmaSlug.from_name(str(once))
    assert str(once) == str(twice)


def test_turma_slug_composes_into_a_path():
    # Usável direto em `DATA_ROOT / slug` (os.PathLike) — sem str() em cada call site.
    assert Path("data") / values.TurmaSlug.from_name("Turma 6") == Path("data/turma-6")


# --- CodeStateId: id do ProgSnap2 que vira NOME DE ARQUIVO no cache ------------------------


def test_code_state_id_accepts_the_shapes_the_dataset_uses():
    for ok in ("c1", "abc-123", "state_42", "v1.2"):
        assert str(values.CodeStateId(ok)) == ok


@pytest.mark.parametrize("bad", ["", "..", "a/b", "../etc", "a b", "c\x00d", "ç"])
def test_code_state_id_rejects_anything_that_could_escape_a_directory(bad):
    with pytest.raises(ValueError):
        values.CodeStateId(bad)


# --- ConfinedPath: resolve-depois-confere sob uma raiz --------------------------------------


def test_confined_path_accepts_a_path_under_the_root(tmp_path):
    target = tmp_path / "clean" / "a.parquet"
    assert Path(values.ConfinedPath(target, root=tmp_path)) == target.resolve()


def test_confined_path_accepts_the_root_itself(tmp_path):
    assert Path(values.ConfinedPath(tmp_path, root=tmp_path)) == tmp_path.resolve()


def test_confined_path_rejects_traversal_out_of_the_root(tmp_path):
    # O caso real (CR-01): main_table="/etc/passwd" viraria leitura arbitrária via pandas.
    with pytest.raises(ValueError):
        values.ConfinedPath(Path("/etc/passwd"), root=tmp_path)
    with pytest.raises(ValueError):
        values.ConfinedPath(tmp_path / ".." / "fora", root=tmp_path)


def test_confined_path_resolves_before_checking(tmp_path):
    # Confere no caminho JÁ resolvido: um ".." no meio que volta para dentro é legítimo e deve
    # passar — a guarda é sobre o destino real, não sobre a aparência da string.
    (tmp_path / "a").mkdir()
    inside = tmp_path / "a" / ".." / "b.parquet"
    assert Path(values.ConfinedPath(inside, root=tmp_path)) == (tmp_path / "b.parquet").resolve()


# --- ProgSnapAssignmentId: o id do ProgSnap2, distinto do id do banco (999.2) ---------------


def test_progsnap_assignment_id_wraps_the_dataset_int():
    assert values.ProgSnapAssignmentId(439).value == 439
    assert str(values.ProgSnapAssignmentId(439)) == "439"


@pytest.mark.parametrize("not_an_int", [None, "439", 439.0, True])
def test_progsnap_assignment_id_refuses_anything_but_an_int(not_an_int):
    # None viraria "assignment_None.parquet" em silêncio; é a coluna vazia de um assignment
    # que não veio da importação.
    with pytest.raises(ValueError):
        values.ProgSnapAssignmentId(not_an_int)


def test_progsnap_assignment_id_is_not_interchangeable_with_a_db_id():
    # O ponto do tipo (999.2): assignment.id == 1 e o ProgSnap2 AssignmentID == 439 são ambos int
    # e significam coisas diferentes. Comparar um com o outro tem de ser falso, não acidentalmente
    # verdadeiro quando os números coincidem.
    progsnap = values.ProgSnapAssignmentId(1)
    assert progsnap.value == 1
    assert progsnap != 1


# --- consolidação: as definições locais somem ----------------------------------------------


@pytest.mark.parametrize(
    "module_name",
    [
        "edmkt_app.train",
        "edmkt_app.mastery_service",
        "edmkt_app.eda",
        "edmkt_app.kc_pipeline",
        "edmkt_app.features_cache",
        "edmkt_app.ingestion.service",
    ],
)
def test_no_module_keeps_its_own_slug_or_progsnap_copy(module_name):
    # A invariante de caminho passa a ter UMA implementação. Enquanto cada módulo mantiver a sua,
    # corrigir uma delas conserta um sexto do problema (o que já aconteceu: utils.py nasceu para
    # ser "a versão PÚBLICA e única" e as 6 cópias continuaram lá).
    import importlib

    module = importlib.import_module(module_name)
    assert not hasattr(module, "_slug")
    assert not hasattr(module, "_progsnap_aid")


def test_ingestion_router_does_not_reach_into_another_modules_private_helper():
    # api/ingestion.py:74 chamava service._slug(...) — exatamente o cruzamento de fronteira que
    # o utils.py existia para impedir.
    import inspect

    from edmkt_app.api import ingestion

    assert "service._slug" not in inspect.getsource(ingestion)
