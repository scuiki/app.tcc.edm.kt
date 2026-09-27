# O domínio por conceito é a média dos problemas dele; nunca gravado, sempre derivado da matriz.

from __future__ import annotations

from api.mastery_dashboard.domain.value_objects.student_mastery_matrix import StudentMasteryMatrix


def aggregate_by_knowledge_component(
    matrix: StudentMasteryMatrix, kcs_by_problem: dict[int, list[int]]
) -> dict[tuple[str, int], float]:
    # Devolve `{(student_id, kc_id): mastery}`; cada problema alimenta todos os conceitos que exige.
    by_student_kc: dict[tuple[str, int], list[float]] = {}
    for (student_id, problem_id), mastery in matrix.items():
        for kc_id in kcs_by_problem.get(problem_id, []):
            by_student_kc.setdefault((student_id, kc_id), []).append(mastery)
    return {key: sum(values) / len(values) for key, values in by_student_kc.items()}
