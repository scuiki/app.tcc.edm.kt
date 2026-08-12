"""Base de use case de escrita + o runner de specifications.

Semântica pedida: roda TODAS as specs, sem short-circuit, e agrega os resultados no fim
(multiRegistryValidation). Um payload com três problemas devolve os três, não o primeiro.

Consequência que a base precisa garantir e o teste pina: como todas rodam, uma spec NÃO pode
assumir que outra passou. `assignment inexistente` não pode fazer a spec seguinte estourar com
AttributeError — cada uma busca o que precisa e tolera ausência.
"""

from __future__ import annotations

import pytest

from edmkt_app.use_cases.base import BaseWriteUseCase, ValidationFailed


class _Spec:
    """Spec de teste: devolve a mensagem configurada e registra que rodou."""

    def __init__(self, message: str | None) -> None:
        self.message = message
        self.ran = 0

    def check(self, conn, dto) -> str | None:
        self.ran += 1
        return self.message


class _Dto:
    pass


def _use_case(conn, specs):
    class _UC(BaseWriteUseCase):
        def _run(self, dto):
            return "executado"

    uc = _UC(conn)
    uc.specs = specs
    return uc


def test_all_specs_run_even_after_the_first_failure(tmp_db):
    a, b, c = _Spec("erro A"), _Spec(None), _Spec("erro C")

    with pytest.raises(ValidationFailed):
        _use_case(tmp_db, [a, b, c]).execute(_Dto())

    assert (a.ran, b.ran, c.ran) == (1, 1, 1)  # nenhuma foi pulada


def test_failure_carries_every_message_in_order(tmp_db):
    specs = [_Spec("erro A"), _Spec(None), _Spec("erro C")]

    with pytest.raises(ValidationFailed) as excinfo:
        _use_case(tmp_db, specs).execute(_Dto())

    assert excinfo.value.messages == ["erro A", "erro C"]


def test_all_passing_specs_let_the_body_run(tmp_db):
    result = _use_case(tmp_db, [_Spec(None), _Spec(None)]).execute(_Dto())

    assert result == "executado"


def test_body_never_runs_when_a_spec_fails(tmp_db):
    ran = []

    class _UC(BaseWriteUseCase):
        def _run(self, dto):
            ran.append(1)
            return None

    uc = _UC(tmp_db)
    uc.specs = [_Spec("erro")]
    with pytest.raises(ValidationFailed):
        uc.execute(_Dto())

    assert ran == []


def test_no_specs_means_nothing_to_validate(tmp_db):
    assert _use_case(tmp_db, []).execute(_Dto()) == "executado"


def test_validation_failed_stringifies_all_messages(tmp_db):
    err = ValidationFailed(["erro A", "erro C"])

    assert "erro A" in str(err) and "erro C" in str(err)
