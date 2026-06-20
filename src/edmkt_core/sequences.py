# Ported from tcc.edm.kt @ 0e8807c — src/data_loader.py (build_sequences, truncate_sequences only)
# KT sequence construction (ProgSnap2). Numerics frozen; characterization tests gate any refactor.
#
# CSEDM loaders (_SPLITS, load_main_table, filter_for_bkt_dkt, filter_for_code_dkt,
# load_labels, load_spring2019_split) are intentionally EXCLUDED (D-05); the split
# logic is extracted to pipeline.py in plan 04.
#
# NOTE (CORE-05): truncate_sequences below recomputes is_first_attempt on the
# truncated window — this is the +13.6pp inflation bug. It is ported VERBATIM here
# so a characterization test pins current behavior; the fix lands in plan 03.

from pathlib import Path  # noqa: F401 — retained from source; harmless, kept for verbatim fidelity
import pandas as pd


def build_sequences(df: pd.DataFrame, assignment_id: int) -> list[dict]:
    #Constrói sequências KT por estudante para um assignment específico.

    assign_df = df[df["AssignmentID"] == assignment_id].copy()

    # Ordenar cronologicamente antes de marcar a primeira tentativa
    assign_df = assign_df.sort_values(
        ["SubjectID", "ServerTimestamp"], kind="stable"
    )

    # is_first_attempt: primeira ocorrência de (SubjectID, ProblemID) no tempo
    assign_df["is_first_attempt"] = ~assign_df.duplicated(
        subset=["SubjectID", "ProblemID"], keep="first"
    )

    sequences = []
    for subject_id, student_df in assign_df.groupby("SubjectID", sort=True):
        sequences.append({
            "subject_id": subject_id,
            "assignment_id": int(assignment_id),
            "events": student_df.reset_index(drop=True),
        })

    return sequences


def truncate_sequences(sequences: list[dict], max_len: int = 50) -> list[dict]:
    #Trunca sequências KT para as últimas max_len tentativas por estudante.

    truncated = []
    for seq in sequences:
        events = seq["events"]
        if len(events) > max_len:
            events = events.iloc[-max_len:].copy()
            events["is_first_attempt"] = ~events.duplicated(
                subset=["ProblemID"], keep="first"
            )
            events = events.reset_index(drop=True)
        truncated.append({
            "subject_id": seq["subject_id"],
            "assignment_id": seq["assignment_id"],
            "events": events,
        })
    return truncated
