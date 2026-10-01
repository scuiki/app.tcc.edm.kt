from __future__ import annotations


class IncompatibleTrainedModelError(Exception):
    # Um modelo gravado noutro formato, que o app não consegue ler sem retreinar
    pass
