# Base dos use cases que mudam estado, valida tudo e só depois age.
from __future__ import annotations

from typing import Any

from api.shared.domain.interfaces.business_rule import IBusinessRule
from api.shared.domain.errors.business_rule_violation import BusinessRuleViolation


class WriteUseCase:
    # As regras que o pedido precisa satisfazer antes de `_run`; por padrão, nenhuma.
    def rules(self) -> list[IBusinessRule]:
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
