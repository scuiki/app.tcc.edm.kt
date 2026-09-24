"""AUC-ROC das previsões de acerto: a métrica primária é a das primeiras tentativas.

Portado do TCC 1 (src/evaluation.py). Numérica congelada.
"""


import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def compute_auc(predictions: pd.DataFrame, first_attempt_only: bool = False) -> float:
    """AUC-ROC agregado sobre as previsões; `first_attempt_only` dá o first-attempt AUC."""

    df = predictions.copy()
    if first_attempt_only:
        df = df[df["is_first_attempt"] == True]

    df = df.dropna(subset=["predicted_correct_probability"])
    if len(df) == 0 or df["is_correct"].nunique() < 2:
        return np.nan

    return float(roc_auc_score(df["is_correct"].astype(int), df["predicted_correct_probability"]))
