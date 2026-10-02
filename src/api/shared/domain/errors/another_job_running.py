from __future__ import annotations


class AnotherJobRunning(Exception):
    # Não é regra de negócio, é condição de corrida; a checagem que vale é o acquire do próprio job.
    pass
