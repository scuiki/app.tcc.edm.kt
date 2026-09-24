# AUC-ROC das previsões (métrica primária é a da primeira tentativa), portado do TCC 1, congelada.


import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def compute_auc(predictions: pd.DataFrame, first_attempt_only: bool = False) -> float:
    # AUC-ROC agregado sobre as previsões; `first_attempt_only` restringe ao first-attempt AUC.

    df = predictions.copy()
    if first_attempt_only:
        df = df[df["is_first_attempt"] == True]

    df = df.dropna(subset=["predicted_correct_probability"])
    if len(df) == 0 or df["is_correct"].nunique() < 2:
        return np.nan

    return float(roc_auc_score(df["is_correct"].astype(int), df["predicted_correct_probability"]))
