# Etapa 1 do KCGen-KT, escolhe até 5 soluções corretas e diversas por problema; ciência congelada.

from __future__ import annotations

import random

import pandas as pd

SEED = 42


def _attempt_bucket(total_attempts: int) -> int:
    # A faixa (1 a 5) do número de tentativas até acertar (Duan et al., 2025).
    if total_attempts <= 1:
        return 1
    if total_attempts <= 3:
        return 2
    if total_attempts <= 6:
        return 3
    if total_attempts <= 10:
        return 4
    return 5


def _first_correct_per_student(problem_df: pd.DataFrame) -> list[dict]:
    # 1ª submissão correta de cada aluno; sem nenhuma submissão correta, o aluno fica de fora.
    events = problem_df.sort_values("submitted_at", kind="stable")
    samples: list[dict] = []
    for _student_id, student_events in events.groupby("student_id", sort=False):
        student_events = student_events.sort_values("submitted_at", kind="stable")
        correct_mask = student_events["is_correct"] == 1
        if not correct_mask.any():
            continue
        first_correct_pos = int(correct_mask.values.argmax())  # tentativas antes da 1ª correta
        first_correct = student_events.iloc[first_correct_pos]
        samples.append({
            "student_id": str(_student_id),
            "code_snapshot_id": str(first_correct["code_snapshot_id"]),
            "total_attempts": first_correct_pos + 1,
            "code": str(first_correct["code"]),
        })
    return samples


def select_sample_solutions(
    problem_df: pd.DataFrame, n: int = 5, rng: random.Random | None = None
) -> list[dict]:
    # Até n soluções corretas, uma por faixa de tentativas (1..5); sorteio semeado, reproduzível.
    if rng is None:
        rng = random.Random(SEED)

    correct_events = _first_correct_per_student(problem_df)

    buckets: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    for event in correct_events:
        buckets[_attempt_bucket(int(event["total_attempts"]))].append(event)

    sampled: list[dict] = []
    for b in (1, 2, 3, 4, 5):
        if len(sampled) >= n:
            break
        if buckets[b]:
            sampled.append(rng.choice(buckets[b]))
    return sampled
