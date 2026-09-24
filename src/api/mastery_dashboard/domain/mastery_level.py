"""As regras de produto do dashboard: faixas de mastery, KCs críticos e alunos em risco.

Não são ciência do modelo: são heurísticas do protótipo para o professor ler a matriz (os limiares
0,40 / 0,70 e "3 ou mais KCs em nível baixo"). Funções puras e determinísticas.
"""

from __future__ import annotations

from enum import StrEnum

LOW_MASTERY_THRESHOLD = 0.40
HIGH_MASTERY_THRESHOLD = 0.70
AT_RISK_LOW_KC_COUNT = 3

StudentMasteryMatrix = dict[tuple[str, int], float]  # {(student_id, kc_id): mastery}


class MasteryLevel(StrEnum):
    LOW = "low"  # abaixo de 0,40
    MEDIUM = "medium"  # de 0,40 a 0,70, inclusive
    HIGH = "high"  # acima de 0,70


def classify_mastery_level(mastery: float) -> MasteryLevel:
    if mastery < LOW_MASTERY_THRESHOLD:
        return MasteryLevel.LOW
    if mastery <= HIGH_MASTERY_THRESHOLD:
        return MasteryLevel.MEDIUM
    return MasteryLevel.HIGH


def find_critical_knowledge_components(matrix: StudentMasteryMatrix) -> list[tuple[int, float]]:
    """(kc_id, mastery média da turma), do KC mais fraco ao mais forte."""
    by_kc: dict[int, list[float]] = {}
    for (_student_id, kc_id), mastery in matrix.items():
        by_kc.setdefault(kc_id, []).append(mastery)

    means = [(kc_id, sum(values) / len(values)) for kc_id, values in by_kc.items()]
    means.sort(key=lambda item: (item[1], item[0]))  # média crescente; kc_id desempata
    return means


def find_students_at_risk(
    matrix: StudentMasteryMatrix, min_low_kcs: int = AT_RISK_LOW_KC_COUNT
) -> list[str]:
    """Os alunos com `min_low_kcs` ou mais KCs em nível baixo, em ordem."""
    low_counts: dict[str, int] = {}
    for (student_id, _kc_id), mastery in matrix.items():
        if classify_mastery_level(mastery) is MasteryLevel.LOW:
            low_counts[student_id] = low_counts.get(student_id, 0) + 1
    return sorted(s for s, n in low_counts.items() if n >= min_low_kcs)
