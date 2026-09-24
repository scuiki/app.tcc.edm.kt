"""Os dois tipos de evento do ProgSnap2 que o app guarda, com os valores exatos do dataset.

`RUN_PROGRAM`: o código rodou e recebeu nota; é o único evento que treino e inferência consomem.
`COMPILE_ERROR`: o código nem compilou; fica no dado limpo porque as estatísticas pré-treino
precisam dele (taxa de erro de compilação).
"""

from __future__ import annotations

import pandas as pd

RUN_PROGRAM = "Run.Program"
COMPILE_ERROR = "Compile.Error"

KEPT_EVENTS = frozenset({RUN_PROGRAM, COMPILE_ERROR})


def keep_only_program_runs(cleaned: pd.DataFrame) -> pd.DataFrame:
    """O recorte que treino e inferência consomem: só os eventos Run.Program.

    Fidelidade a Shi et al. 2022 / TCC 1: o Code-DKT foi treinado só sobre Run.Program. Manter os
    Compile.Error injeta eventos rotulados como erro cujo Java não compila (logo sem AST path) e
    afasta a aplicação do oráculo: no CSEDM real eles são 57,6% das linhas do A439, e treinar com
    eles derrubou o first-attempt AUC para 0,6959, fora da banda de ±3pp.

    NÃO altera o DataFrame recebido: o dado limpo segue inteiro para as estatísticas pré-treino. O
    índice é reconstruído porque quem consome isto adiante itera por posição.
    """
    return cleaned[cleaned["event_type"] == RUN_PROGRAM].copy().reset_index(drop=True)
