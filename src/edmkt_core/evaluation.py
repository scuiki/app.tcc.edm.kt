# Ported from tcc.edm.kt @ 0e8807c — src/evaluation.py
# Shared KT evaluation utilities (DKT/Code-DKT). Numerics frozen; characterization tests gate any refactor.

#Utilitários de avaliação compartilhados entre DKT e Code-DKT.


import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def build_problem_index(sequences_all: list[dict]) -> dict[int, int]:
    #Mapeia ProblemID para índice inteiro via global scan de todas as sequências.

    problem_ids: set[int] = set()
    for seq in sequences_all:
        for pid in seq["events"]["ProblemID"].unique():
            problem_ids.add(int(pid))
    return {pid: idx for idx, pid in enumerate(sorted(problem_ids))}


def compute_auc(pred_df: pd.DataFrame, first_attempt_only: bool = False) -> float:
    #Calcula AUC-ROC pooled sobre predições de qualquer modelo KT.

    df = pred_df.copy()
    if first_attempt_only:
        df = df[df["is_first_attempt"] == True]

    df = df.dropna(subset=["correct_predictions"])
    if len(df) == 0 or df["correct"].nunique() < 2:
        return np.nan

    return float(roc_auc_score(df["correct"].astype(int), df["correct_predictions"]))
