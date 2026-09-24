"""A sequência de tentativas de cada aluno num assignment: a entrada do knowledge tracing.

Portado do TCC 1 (src/data_loader.py). A numérica é congelada; os testes de caracterização ao lado
travam qualquer mudança.

`is_first_attempt` é calculado UMA vez, sobre a sequência completa e ordenada, e só carregado
adiante pelo truncamento. O port literal recalculava a flag dentro da janela truncada, o que
inflava o first-attempt AUC em 13,6 pontos.
"""

import pandas as pd


def build_student_sequences(df: pd.DataFrame, progsnap_assignment_id: int) -> list[dict]:
    """Uma sequência por aluno, em ordem cronológica, com `is_first_attempt` marcado."""

    assign_df = df[df["progsnap_assignment_id"] == progsnap_assignment_id].copy()

    # Ordenar cronologicamente antes de marcar a primeira tentativa
    assign_df = assign_df.sort_values(
        ["student_id", "submitted_at"], kind="stable"
    )

    # is_first_attempt: primeira ocorrência de (aluno, problema) no tempo
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
    """Mantém só as últimas `max_len` tentativas de cada aluno."""

    truncated = []
    for seq in sequences:
        events = seq["events"]
        if len(events) > max_len:
            # Só fatia: is_first_attempt veio da sequência completa e não pode ser recalculado
            # na janela.
            events = events.iloc[-max_len:].copy()
            events = events.reset_index(drop=True)
        truncated.append({
            "student_id": seq["student_id"],
            "progsnap_assignment_id": seq["progsnap_assignment_id"],
            "events": events,
        })
    return truncated
