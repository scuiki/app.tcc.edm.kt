from __future__ import annotations


class BusinessRuleViolation(Exception):
    """Uma ou mais regras de negócio recusaram o pedido. Carrega TODAS as mensagens."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("; ".join(messages))
