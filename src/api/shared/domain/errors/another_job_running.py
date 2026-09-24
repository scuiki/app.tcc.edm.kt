from __future__ import annotations


class AnotherJobRunning(Exception):
    # Não é regra de negócio, é corrida; o gate autoritativo é o acquire dentro do próprio job.
    pass
