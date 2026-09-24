"""As recusas que o domínio e os use cases levantam. Nenhuma conhece HTTP.

Quem traduz cada uma para status code é `shared/presentation/http/error_handlers.py`.
"""

from __future__ import annotations


class NotFound(Exception):
    """O recurso alvo não existe.

    Categoria distinta de regra violada: um endpoint distingue as duas (404 contra 409). Não
    acumula com as regras: se o alvo não existe, não há sobre o que aplicar as demais.
    """


class BusinessRuleViolation(Exception):
    """Uma ou mais regras de negócio recusaram o pedido. Carrega TODAS as mensagens."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("; ".join(messages))


class AnotherJobRunning(Exception):
    """Já há um job pesado rodando (treino, geração de KCs ou importação).

    NÃO é uma regra de negócio: é corrida, não defeito do pedido. O gate autoritativo é o acquire
    da OneJobAtATimeLock dentro do próprio job; tratar isto como regra convidaria alguém a
    concluir que o gate está no web e apagar aquele acquire.
    """
