# Ported from tcc.edm.kt @ 0e8807c — src/data_loader.py (build_sequences, truncate_sequences only)
# KT sequence construction (ProgSnap2). Numerics frozen; characterization tests gate any refactor.
#
# CSEDM loaders (_SPLITS, load_main_table, filter_for_bkt_dkt, filter_for_code_dkt,
# load_labels, load_spring2019_split) are intentionally EXCLUDED (D-05); the split
# logic is extracted to pipeline.py in plan 04.
#
# CORE-05: is_first_attempt is derived once in build_sequences on the full ordered
# sequence and carried immutably through truncate_sequences, which now slices only.
# (The verbatim port recomputed the flag in-window — the +13.6pp inflation bug; fixed.)

import pandas as pd


def build_sequences(df: pd.DataFrame, assignment_id: int) -> list[dict]:
    #Constrói sequências KT por estudante para um assignment específico.

    assign_df = df[df["progsnap_assignment_id"] == assignment_id].copy()

    # Ordenar cronologicamente antes de marcar a primeira tentativa
    assign_df = assign_df.sort_values(
        ["student_id", "submitted_at"], kind="stable"
    )

    # is_first_attempt: primeira ocorrência de (SubjectID, ProblemID) no tempo
    assign_df["is_first_attempt"] = ~assign_df.duplicated(
        subset=["student_id", "problem_id"], keep="first"
    )

    sequences = []
    for subject_id, student_df in assign_df.groupby("student_id", sort=True):
        sequences.append({
            "student_id": subject_id,
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
            # Slice only — is_first_attempt was derived on the full ordered sequence
            # in build_sequences and must not be recomputed on the window (CORE-05).
            events = events.iloc[-max_len:].copy()
            events = events.reset_index(drop=True)
        truncated.append({
            "student_id": seq["student_id"],
            "assignment_id": seq["assignment_id"],
            "events": events,
        })
    return truncated
