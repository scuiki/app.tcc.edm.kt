from __future__ import annotations


class AnotherJobRunning(Exception):
    """Já há um job pesado rodando (treino, geração de KCs ou importação).

    NÃO é uma regra de negócio: é corrida, não defeito do pedido. O gate autoritativo é o acquire
    da OneJobAtATimeLock dentro do próprio job; tratar isto como regra convidaria alguém a
    concluir que o gate está no web e apagar aquele acquire.
    """
