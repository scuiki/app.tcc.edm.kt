"""As regras de produto do dashboard: faixas de mastery, KCs críticos e alunos em risco.

Não são ciência do modelo, são heurísticas do protótipo para o professor ler a matriz (os limiares
0,40 / 0,70 e o "3 ou mais KCs em nível baixo"). Por isso moram na aplicação e não em `ml/`.
Funções puras: dict in -> list out, determinísticas.
"""

from __future__ import annotations

# Fixed prototype heuristic (REQUIREMENTS:85, D-63): kept module-level so the dashboard layer can
# read/override them without re-deriving the cutoffs.
LOW_MASTERY_THRESHOLD = 0.40
HIGH_MASTERY_THRESHOLD = 0.70
AT_RISK_LOW_KC_COUNT = 3


def classify_mastery_level(mastery: float) -> str:
    """O MasteryLevel de um valor: low <0.40, medium [0.40, 0.70], high >0.70 (DASH-01)."""
    if mastery < LOW_MASTERY_THRESHOLD:
        return "low"
    if mastery <= HIGH_MASTERY_THRESHOLD:
        return "medium"
    return "high"


def find_critical_knowledge_components(matrix: dict[tuple[str, int], float]) -> list[tuple[int, float]]:
    """KCs ranked ascending by mean class mastery — weakest first (DASH-02)."""
    by_kc: dict[int, list[float]] = {}
    for (_student_id, kc_id), mastery in matrix.items():
        by_kc.setdefault(kc_id, []).append(mastery)

    means = [(kc_id, sum(v) / len(v)) for kc_id, v in by_kc.items()]
    means.sort(key=lambda item: (item[1], item[0]))  # mean asc; kc_id breaks ties deterministically
    return means


def find_students_at_risk(
    matrix: dict[tuple[str, int], float], min_low_kcs: int = AT_RISK_LOW_KC_COUNT
) -> list[str]:
    """Students with ≥ min_low_kcs KCs below the low band (<0.40) (DASH-03)."""
    low_counts: dict[str, int] = {}
    for (student_id, _kc_id), mastery in matrix.items():
        if classify_mastery_level(mastery) == "low":
            low_counts[student_id] = low_counts.get(student_id, 0) + 1

    return sorted(s for s, n in low_counts.items() if n >= min_low_kcs)
