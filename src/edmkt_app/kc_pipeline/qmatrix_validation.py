"""A guarda ≥1 KC por problema (KC-04): validar-tudo-depois-persistir promovido a falha-dura."""

from __future__ import annotations

import pandas as pd

from edmkt_app.llm.validation import EmptyContentError


def _validate_qmatrix(qmatrix: pd.DataFrame, problem_ids: list[str]) -> None:
    """≥1 KC por problema na Q-matrix completa (KC-04). Falha ⇒ EmptyContentError ⇒ hard-fail.

    É o "validar tudo, depois persistir" promovido a falha-dura de job (D-04): uma linha
    toda-zero (problema sem nenhum KC mapeado) reprova a Q-matrix inteira — nada parcial entra."""
    if not problem_ids or qmatrix.empty:
        raise EmptyContentError("Q-matrix vazia: nenhum problema correto gerou KCs")
    for pid in problem_ids:
        if int(qmatrix.loc[pid].sum()) < 1:
            raise EmptyContentError(f"problema {pid} ficou sem nenhum KC")
