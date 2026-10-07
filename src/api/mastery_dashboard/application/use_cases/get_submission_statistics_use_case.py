# O bloco "o que aconteceu", disponível desde a importação; os conceitos só depois de aprovados.

from __future__ import annotations

from api.assignments.domain.value_objects.assignment_status import AssignmentStatus
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.services.existing_assignment import get_existing_assignment
from api.classroom_import.domain.interfaces.submission_repository import ISubmissionRepository
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)
from api.mastery_dashboard.application.dtos.mastery_dashboard_dto import (
    KnowledgeComponentRefDTO,
    KnowledgeComponentStatisticsDTO,
    ProblemStatisticsDTO,
    SubmissionStatisticsResponseDTO,
)
from api.mastery_dashboard.domain.services.submission_statistics_calculation import (
    compute_knowledge_component_statistics,
    compute_problem_statistics,
    compute_student_activity,
)

_WITH_APPROVED_CONCEPTS = (AssignmentStatus.KC_APPROVED, AssignmentStatus.TRAINED)


class GetSubmissionStatisticsUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        submissions: ISubmissionRepository,
        knowledge_components: IKnowledgeComponentRepository,
        problem_kcs: IProblemKnowledgeComponentRepository,
    ) -> None:
        self._assignments = assignments
        self._submissions = submissions
        self._knowledge_components = knowledge_components
        self._problem_kcs = problem_kcs

    def execute(self, assignment_id: int) -> SubmissionStatisticsResponseDTO:
        assignment = get_existing_assignment(self._assignments, assignment_id)
        # Lê o dado inteiro, com Compile.Error, do qual os erros de compilação dependem.
        submissions = self._submissions.list_by_assignment(assignment_id)

        kcs_by_problem: dict[int, list[int]] = {}
        names: dict[int, str] = {}
        if assignment.status in _WITH_APPROVED_CONCEPTS:
            names = {kc.id: kc.name for kc in self._knowledge_components.list_by_assignment(assignment_id)}
            for binding in self._problem_kcs.list_by_assignment(assignment_id):
                kcs_by_problem.setdefault(binding.problem_id, []).append(binding.kc_id)
        problems_by_kc: dict[int, list[int]] = {}
        for problem_id, kc_ids in kcs_by_problem.items():
            for kc_id in kc_ids:
                problems_by_kc.setdefault(kc_id, []).append(problem_id)

        return SubmissionStatisticsResponseDTO(
            assignment_id=assignment_id,
            student_count=len(compute_student_activity(submissions)),
            problems=[
                ProblemStatisticsDTO(
                    problem_id=p.problem_id,
                    success_rate=p.success_rate,
                    median_attempts_to_complete=p.median_attempts_to_complete,
                    students_attempted=p.students_attempted,
                    students_completed=p.students_completed,
                    compile_errors_per_run=p.compile_errors_per_run,
                    kcs=[
                        KnowledgeComponentRefDTO(kc_id=kc_id, kc_name=names.get(kc_id, f"KC {kc_id}"))
                        for kc_id in sorted(kcs_by_problem.get(p.problem_id, []))
                    ],
                )
                for p in compute_problem_statistics(submissions)
            ],
            knowledge_components=[
                KnowledgeComponentStatisticsDTO(
                    kc_id=k.kc_id,
                    kc_name=names.get(k.kc_id, f"KC {k.kc_id}"),
                    problem_ids=sorted(problems_by_kc[k.kc_id]),
                    success_rate=k.success_rate,
                    runs=k.runs,
                )
                for k in compute_knowledge_component_statistics(submissions, kcs_by_problem)
            ],
        )
