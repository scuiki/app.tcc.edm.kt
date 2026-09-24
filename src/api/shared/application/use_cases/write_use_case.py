"""Base dos use cases que MUDAM estado: validar tudo, depois agir.

As regras rodam todas e se acumulam, sem short-circuit: um pedido com três problemas devolve os
três, em vez de obrigar o professor a descobrir um por vez. Leitura não estende esta base; não há
o que validar antes de ler.
"""

from __future__ import annotations

from typing import Any

from api.shared.domain.interfaces.business_rule import IBusinessRule
from api.shared.domain.errors.business_rule_violation import BusinessRuleViolation


class WriteUseCase:
    def rules(self) -> list[IBusinessRule]:
        """As regras que o pedido tem de satisfazer antes de `_run`. Default: nenhuma."""
        return []

    def validate(self, dto: Any) -> None:
        refusals = [message for rule in self.rules() if (message := rule.check(dto)) is not None]
        if refusals:
            raise BusinessRuleViolation(refusals)

    def execute(self, dto: Any) -> Any:
        self.validate(dto)
        return self._run(dto)

    def _run(self, dto: Any) -> Any:
        raise NotImplementedError
