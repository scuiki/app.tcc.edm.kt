"""ClassroomSlug: o nome arbitrário da turma vira um componente de caminho seguro."""

from __future__ import annotations

from pathlib import Path

from api.assignments.domain.classroom_slug import ClassroomSlug


def test_classroom_slug_normalizes():
    assert str(ClassroomSlug.from_name("Turma 6")) == "turma-6"
    assert str(ClassroomSlug.from_name("CSEDM Spring 2019")) == "csedm-spring-2019"


def test_classroom_slug_collapses_unsafe_characters():
    # O nome vem do professor: qualquer coisa fora de [a-z0-9] colapsa em "-", então nenhum
    # separador de caminho, "..", ou byte exótico sobrevive para virar diretório.
    slug = str(ClassroomSlug.from_name("../etc/passwd"))
    assert "/" not in slug and ".." not in slug


def test_classroom_slug_falls_back_when_nothing_survives():
    assert str(ClassroomSlug.from_name("   ")) == "classroom"
    assert str(ClassroomSlug.from_name("!!!")) == "classroom"


def test_classroom_slug_is_idempotent():
    # Idempotente: slugificar um slug devolve ele mesmo, então aplicar duas vezes é inofensivo.
    once = ClassroomSlug.from_name("Turma 6")
    twice = ClassroomSlug.from_name(str(once))
    assert str(once) == str(twice)


def test_classroom_slug_composes_into_a_path():
    # Usável direto em `DATA_ROOT / slug` (os.PathLike) — sem str() em cada call site.
    assert Path("data") / ClassroomSlug.from_name("Turma 6") == Path("data/turma-6")


# --- CodeStateId: id do ProgSnap2 que vira NOME DE ARQUIVO no cache ------------------------
