"""WriteUseCase: roda TODAS as regras, sem short-circuit, e acumula as recusas.

Um pedido com três problemas devolve os três, não o primeiro. Como todas rodam, uma regra NÃO pode
assumir que outra passou; cada uma busca o que precisa e tolera ausência.
"""

from __future__ import annotations

import pytest

from api.shared.application.write_use_case import WriteUseCase
from api.shared.domain.errors import BusinessRuleViolation


class _Rule:
    """Regra de teste: devolve a mensagem configurada e registra que rodou."""

    def __init__(self, message: str | None) -> None:
        self.message = message
        self.ran = 0

    def check(self, dto) -> str | None:
        self.ran += 1
        return self.message


class _Dto:
    pass


class _UseCase(WriteUseCase):
    def __init__(self, rules: list[_Rule]) -> None:
        self._rules = rules
        self.ran = 0

    def rules(self) -> list[_Rule]:
        return self._rules

    def _run(self, dto) -> str:
        self.ran += 1
        return "executado"


def test_all_rules_run_even_after_the_first_refusal():
    a, b, c = _Rule("erro A"), _Rule(None), _Rule("erro C")

    with pytest.raises(BusinessRuleViolation):
        _UseCase([a, b, c]).execute(_Dto())

    assert (a.ran, b.ran, c.ran) == (1, 1, 1)  # nenhuma foi pulada


def test_the_violation_carries_every_refusal_in_order():
    with pytest.raises(BusinessRuleViolation) as excinfo:
        _UseCase([_Rule("erro A"), _Rule(None), _Rule("erro C")]).execute(_Dto())

    assert excinfo.value.messages == ["erro A", "erro C"]


def test_when_every_rule_passes_the_body_runs():
    assert _UseCase([_Rule(None), _Rule(None)]).execute(_Dto()) == "executado"


def test_the_body_never_runs_when_a_rule_refuses():
    use_case = _UseCase([_Rule("erro")])

    with pytest.raises(BusinessRuleViolation):
        use_case.execute(_Dto())

    assert use_case.ran == 0


def test_no_rules_means_nothing_to_validate():
    class _NoRules(WriteUseCase):
        def _run(self, dto) -> str:
            return "executado"

    assert _NoRules().execute(_Dto()) == "executado"


def test_the_violation_stringifies_every_message():
    violation = BusinessRuleViolation(["erro A", "erro C"])

    assert "erro A" in str(violation) and "erro C" in str(violation)
