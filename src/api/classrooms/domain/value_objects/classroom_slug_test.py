# ClassroomSlug transforma o nome arbitrário da turma num componente de caminho seguro.

from __future__ import annotations


from api.classrooms.domain.value_objects.classroom_slug import ClassroomSlug


def test_classroom_slug_normalizes():
    assert str(ClassroomSlug.from_name("Turma 6")) == "turma-6"
    assert str(ClassroomSlug.from_name("CSEDM Spring 2019")) == "csedm-spring-2019"


def test_classroom_slug_collapses_unsafe_characters():
    # Qualquer caractere fora de [a-z0-9] colapsa em "-", então nada sobrevive para virar diretório.
    slug = str(ClassroomSlug.from_name("../etc/passwd"))
    assert "/" not in slug and ".." not in slug


def test_classroom_slug_falls_back_when_nothing_survives():
    assert str(ClassroomSlug.from_name("   ")) == "classroom"
    assert str(ClassroomSlug.from_name("!!!")) == "classroom"


def test_classroom_slug_is_idempotent():
    # Idempotente, slugificar um slug devolve ele mesmo, então aplicar duas vezes é inofensivo.
    once = ClassroomSlug.from_name("Turma 6")
    twice = ClassroomSlug.from_name(str(once))
    assert str(once) == str(twice)
