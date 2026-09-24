"""Índice de problemas: cada problem_id vira uma posição fixa na saída do modelo."""

# Ported from tcc.edm.kt @ 0e8807c — src/evaluation.py (build_problem_index).


def build_problem_index(sequences: list[dict]) -> dict[int, int]:
    """problem_id -> posição na saída do modelo, varrendo todas as sequências."""

    problem_ids: set[int] = set()
    for seq in sequences:
        for pid in seq["events"]["problem_id"].unique():
            problem_ids.add(int(pid))
    return {pid: idx for idx, pid in enumerate(sorted(problem_ids))}
