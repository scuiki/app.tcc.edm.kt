# Sequência de tentativas de cada aluno, adaptada do TCC 1 (src/data_loader.py).

import pandas as pd


ATTEMPT_ORDERS = ("time", "file")


def build_student_sequences(
    df: pd.DataFrame, progsnap_assignment_id: int, attempt_order: str = "time"
) -> list[dict]:
    # Uma sequência por aluno, na attempt_order pedida, com is_first_attempt marcado.

    if attempt_order not in ATTEMPT_ORDERS:
        raise ValueError(f"attempt_order {attempt_order!r} não é uma de {ATTEMPT_ORDERS}")

    assign_df = df[df["progsnap_assignment_id"] == progsnap_assignment_id].copy()

    # Ordenar antes de marcar a primeira tentativa, e o sort estável mantém as linhas no empate
    sort_keys = ["student_id", "submitted_at"] if attempt_order == "time" else ["student_id"]
    assign_df = assign_df.sort_values(sort_keys, kind="stable")

    # is_first_attempt marca a primeira ocorrência de (aluno, problema) na sequência
    assign_df["is_first_attempt"] = ~assign_df.duplicated(
        subset=["student_id", "problem_id"], keep="first"
    )

    sequences = []
    for student_id, student_df in assign_df.groupby("student_id", sort=True):
        sequences.append({
            "student_id": student_id,
            "progsnap_assignment_id": int(progsnap_assignment_id),
            "events": student_df.reset_index(drop=True),
        })

    return sequences


def truncate_student_sequences(sequences: list[dict], max_len: int = 50) -> list[dict]:
    # Mantém só as últimas max_len tentativas de cada aluno.

    truncated = []
    for seq in sequences:
        events = seq["events"]
        if len(events) > max_len:
            # Só fatia; recalcular is_first_attempt na janela truncada inflou o AUC em 13,6pp.
            events = events.iloc[-max_len:].copy()
            events = events.reset_index(drop=True)
        truncated.append({
            "student_id": seq["student_id"],
            "progsnap_assignment_id": seq["progsnap_assignment_id"],
            "events": events,
        })
    return truncated
