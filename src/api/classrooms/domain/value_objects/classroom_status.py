# A situação da turma na tela, calculada dos assignments dela e nunca gravada.

from __future__ import annotations

from enum import StrEnum


class ClassroomStatus(StrEnum):
    AWAITING_DATA = "awaiting_data"  # nenhum problema importado
    IN_PROGRESS = "in_progress"  # tem dados, nenhum modelo publicado
    TRAINED = "trained"  # ao menos um assignment com modelo publicado
