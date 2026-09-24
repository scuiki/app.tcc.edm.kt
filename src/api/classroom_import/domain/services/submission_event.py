# RUN_PROGRAM é o único evento que treino/inferência usa; COMPILE_ERROR fica para as estatísticas.

from __future__ import annotations

import pandas as pd

RUN_PROGRAM = "Run.Program"
COMPILE_ERROR = "Compile.Error"

KEPT_EVENTS = frozenset({RUN_PROGRAM, COMPILE_ERROR})


def keep_only_program_runs(cleaned: pd.DataFrame) -> pd.DataFrame:
    # Fiel a Shi et al. 2022; incluir Compile.Error derrubou o first-attempt AUC, fora da banda.
    return cleaned[cleaned["event_type"] == RUN_PROGRAM].copy().reset_index(drop=True)
