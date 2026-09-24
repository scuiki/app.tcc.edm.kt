# A importação é dona desta limpeza; o ml/ não filtra evento, não binariza score nem trata órfão.

from __future__ import annotations

import pandas as pd

from api.classroom_import.domain.value_objects.import_report import ImportCheck
from api.classroom_import.domain.services.submission_event import KEPT_EVENTS, RUN_PROGRAM

# A tradução ProgSnap2 -> glossário acontece só aqui; o resto do sistema lê nomes do glossário.
PROGSNAP_TO_CLEANED_COLUMNS = {
    "SubjectID": "student_id",
    "AssignmentID": "progsnap_assignment_id",
    "ProblemID": "problem_id",
    "CodeStateID": "code_snapshot_id",
    "Code": "code",
    "Score": "score",
    "ServerTimestamp": "submitted_at",
    "EventType": "event_type",
}

# Contrato de colunas para build_student_sequences/train_and_evaluate; a ordem é estável.
CLEANED_COLUMNS = [*PROGSNAP_TO_CLEANED_COLUMNS.values(), "is_correct"]


def clean_submissions(
    raw: pd.DataFrame, code_by_snapshot: dict[str, str]
) -> tuple[pd.DataFrame, list[ImportCheck]]:
    # `code_by_snapshot` é o dict `{CodeStateID: Code}` usado no join e na checagem de integridade.
    checks: list[ImportCheck] = []

    # O filtro de EventType já é o dedup, pois Compile plain some junto do Run.Program.
    n_before = len(raw)
    df = raw[raw["EventType"].isin(KEPT_EVENTS)].copy()
    n_dropped = n_before - len(df)
    if n_dropped:
        checks.append(
            ImportCheck(
                check="dedup_compile",
                severity="warning",
                message=f"{n_dropped} evento(s) Compile plain descartado(s) no dedup mesmo-timestamp.",
                count=n_dropped,
            )
        )

    # `is_correct` é derivada à parte; a coluna Score crua segue intacta para as estatísticas.
    df["is_correct"] = (
        (df["EventType"] == RUN_PROGRAM) & (df["Score"] == 1.0)
    ).astype(int)

    # CodeStateID órfão é dropado, warning e não fatal; o `Code` cru nunca vai pro ImportCheck.
    known = set(code_by_snapshot)
    mask_orphan = ~df["CodeStateID"].astype(str).isin(known)
    n_orphan = int(mask_orphan.sum())
    if n_orphan:
        df = df[~mask_orphan].copy()
        checks.append(
            ImportCheck(
                check="orphan_codestate",
                severity="warning",
                message=f"{n_orphan} evento(s) com CodeStateID órfão descartado(s) — sem snapshot em CodeStates.",
                count=n_orphan,
            )
        )

    # Join por CodeStateID, como no TCC 1; depois do drop dos órfãos o map nunca dá NaN.
    df["Code"] = df["CodeStateID"].astype(str).map(code_by_snapshot)

    cleaned = df.rename(columns=PROGSNAP_TO_CLEANED_COLUMNS)
    return cleaned[CLEANED_COLUMNS].reset_index(drop=True), checks
