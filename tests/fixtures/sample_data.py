# Dado sintético dos testes, gerado em código e nunca lido do CSEDM real.

from __future__ import annotations

import pandas as pd

ASSIGNMENT_ID = 439

JAVA_OK_A = "public int f(int x) { return x + 1; }"
JAVA_OK_B = "public int g(int a, int b) { int s = a + b; return s; }"
JAVA_OK_C = "public boolean h(int n) { if (n > 0) { return true; } return false; }"
# Java quebrado de propósito, para o parser devolver lista vazia sem levantar erro
JAVA_BAD = "public int oops( { return ;;; }"
# O javalang aceita, mas não há par de folhas, então não sai nenhum path
JAVA_EMPTY_CLASS = "class C {}"


def cleaned_row(student, problem, submitted_at, event, score, code, snapshot_id) -> dict:
    # O rótulo segue a regra do Code-DKT, e Compile.Error nunca conta como acerto
    return {
        "student_id": student,
        "problem_id": problem,
        "progsnap_assignment_id": ASSIGNMENT_ID,
        "submitted_at": submitted_at,
        "event_type": event,
        "score": score,
        "code_snapshot_id": snapshot_id,
        "code": code,
        "is_correct": int(event == "Run.Program" and score == 1.0),
    }


def with_cleaned_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")
    return df


def as_progsnap_upload(cleaned: pd.DataFrame) -> pd.DataFrame:
    # O dado limpo de volta à forma do upload do professor, com os nomes do ProgSnap2
    from api.classroom_import.domain.services.submission_cleaning import PROGSNAP_TO_CLEANED_COLUMNS

    to_progsnap = {new: old for old, new in PROGSNAP_TO_CLEANED_COLUMNS.items()}
    return cleaned.drop(columns=["is_correct"]).rename(columns=to_progsnap)
