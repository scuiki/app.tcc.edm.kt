# A leitura por aluno, a média dos problemas e os conceitos em que ele está mais fraco.

from __future__ import annotations

from api.mastery_dashboard.domain.value_objects.student_mastery_matrix import StudentMasteryMatrix

WEAKEST_COUNT = 3


def mean_mastery_by_student(matrix: StudentMasteryMatrix) -> dict[str, float]:
    # A média dos problemas do exercício, sem passar por conceito.
    by_student: dict[str, list[float]] = {}
    for (student_id, _problem_id), mastery in matrix.items():
        by_student.setdefault(student_id, []).append(mastery)
    return {student_id: sum(values) / len(values) for student_id, values in by_student.items()}


def weakest_knowledge_components(
    masteries: dict[int, float], count: int = WEAKEST_COUNT
) -> list[tuple[int, float]]:
    # Os `count` conceitos de menor domínio, do menor para o maior; kc_id desempata.
    return sorted(masteries.items(), key=lambda item: (item[1], item[0]))[:count]
