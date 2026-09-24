"""Os dois tipos de evento do ProgSnap2 que o app guarda, com os valores exatos do dataset.

`RUN_PROGRAM`: o código rodou e recebeu nota; é o único evento que treino e inferência consomem.
`COMPILE_ERROR`: o código nem compilou; fica no dado limpo porque as estatísticas pré-treino
precisam dele (taxa de erro de compilação).
"""

from __future__ import annotations

RUN_PROGRAM = "Run.Program"
COMPILE_ERROR = "Compile.Error"

KEPT_EVENTS = frozenset({RUN_PROGRAM, COMPILE_ERROR})
