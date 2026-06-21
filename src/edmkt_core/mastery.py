# Pure student×KC mastery aggregation in the qmatrix.py style: pandas/dict in → dict/list out,
# deterministic, no I/O / SQL / torch device / LLM (DIP — model load + persistence is plan 06-05).
# Adapts the research concept_map + groupby-mean contract (analyze_kc_difficulty_codedkt.py) to
# in-app Q-matrix rows, never indexing the Code-DKT head by kc_id (Pitfall 2: the head is per-ProblemID).

from __future__ import annotations

import pandas as pd

# Fixed prototype heuristic (REQUIREMENTS:85, D-63): kept module-level so the dashboard layer can
# read/override them without re-deriving the cutoffs.
BAND_LOW = 0.40
BAND_HIGH = 0.70
AT_RISK_KC_THRESHOLD = 3


def classify_band(mastery: float) -> str:
    """Band of a mastery value: low <0.40, medium [0.40, 0.70], high >0.70 (DASH-01)."""
    if mastery < BAND_LOW:
        return "low"
    if mastery <= BAND_HIGH:
        return "medium"
    return "high"


def build_mastery_matrix(
    pred_df: pd.DataFrame, qmatrix: dict[int, list[int]]
) -> dict[tuple[str, int], float]:
    """student×KC matrix {(subject_id, kc_id): mastery} from predict_code_dkt output + Q-matrix.

    A problem's mastery is the LAST `correct_predictions` per (user_id, ProblemID); a KC's mastery
    is the mean over the problems that KC tags (D-04). `skill_name` is str(ProblemID); the qmatrix
    keys are int problem ids, so we coerce to int to join the two.
    """
    if pred_df.empty:
        return {}

    # Last row wins per (user, problem) — a later attempt overrides an earlier first attempt.
    last = pred_df.groupby(["user_id", "skill_name"], sort=False)["correct_predictions"].last()

    matrix: dict[tuple[str, int], float] = {}
    # accumulate per (user, kc): list of the problem masteries that KC tags
    by_user_kc: dict[tuple[str, int], list[float]] = {}
    for (user_id, skill_name), mastery in last.items():
        problem_id = int(skill_name)
        for kc_id in qmatrix.get(problem_id, []):
            by_user_kc.setdefault((user_id, kc_id), []).append(float(mastery))

    for key, values in by_user_kc.items():
        matrix[key] = sum(values) / len(values)
    return matrix


def critical_kcs(matrix: dict[tuple[str, int], float]) -> list[tuple[int, float]]:
    """KCs ranked ascending by mean class mastery — weakest first (DASH-02)."""
    by_kc: dict[int, list[float]] = {}
    for (_subject_id, kc_id), mastery in matrix.items():
        by_kc.setdefault(kc_id, []).append(mastery)

    means = [(kc_id, sum(v) / len(v)) for kc_id, v in by_kc.items()]
    means.sort(key=lambda item: (item[1], item[0]))  # mean asc; kc_id breaks ties deterministically
    return means


def at_risk_students(
    matrix: dict[tuple[str, int], float], threshold_n: int = AT_RISK_KC_THRESHOLD
) -> list[str]:
    """Students with ≥ threshold_n KCs below the low band (<0.40) (DASH-03)."""
    low_counts: dict[str, int] = {}
    for (subject_id, _kc_id), mastery in matrix.items():
        if classify_band(mastery) == "low":
            low_counts[subject_id] = low_counts.get(subject_id, 0) + 1

    return sorted(s for s, n in low_counts.items() if n >= threshold_n)
