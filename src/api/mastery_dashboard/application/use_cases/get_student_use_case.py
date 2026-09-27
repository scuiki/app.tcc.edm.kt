# O detalhe de um aluno para o diálogo, o previsto por conceito e por problema mais o que ele fez.

from __future__ import annotations

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
    StudentDetailDTO,
    StudentKnowledgeComponentMasteryDTO,
    StudentProblemMasteryDTO,
)
from api.mastery_dashboard.application.services.concept_bindings import load_concept_bindings
from api.mastery_dashboard.application.services.published_model_mastery import PublishedModelMastery
from api.mastery_dashboard.domain.services.mastery_by_knowledge_component import (
    aggregate_by_knowledge_component,
)
from api.mastery_dashboard.domain.services.student_mastery import mean_mastery_by_student
from api.mastery_dashboard.domain.services.submission_statistics_calculation import (
    compute_student_activity,
)
from api.shared.domain.errors.not_found import NotFound


class GetStudentUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        submissions: ISubmissionRepository,
        knowledge_components: IKnowledgeComponentRepository,
        problem_kcs: IProblemKnowledgeComponentRepository,
        mastery: PublishedModelMastery,
    ) -> None:
        self._assignments = assignments
        self._submissions = submissions
        self._knowledge_components = knowledge_components
        self._problem_kcs = problem_kcs
        self._mastery = mastery

    def execute(self, assignment_id: int, student_id: str) -> StudentDetailDTO:
        assignment = get_existing_assignment(self._assignments, assignment_id)
        matrix, _model = self._mastery.of(assignment)
        problems = {p: m for (s, p), m in matrix.items() if s == student_id}
        if not problems:
            raise NotFound("aluno inexistente")
        concepts = load_concept_bindings(assignment_id, self._knowledge_components, self._problem_kcs)
        done = compute_student_activity(self._submissions.list_by_assignment(assignment_id)).get(
            student_id
        )
        by_kc = {
            kc_id: mastery
            for (_student_id, kc_id), mastery in aggregate_by_knowledge_component(
                {(student_id, p): m for p, m in problems.items()}, concepts.kcs_by_problem
            ).items()
        }
        return StudentDetailDTO(
            student_id=student_id,
            mean_mastery=mean_mastery_by_student(matrix)[student_id],
            completed=done.completed if done else 0,
            attempted=done.attempted if done else 0,
            runs=done.runs if done else 0,
            compile_errors=done.compile_errors if done else 0,
            knowledge_components=[
                StudentKnowledgeComponentMasteryDTO(
                    kc_id=kc_id, kc_name=concepts.name_of(kc_id), mastery=mastery
                )
                for kc_id, mastery in sorted(by_kc.items(), key=lambda item: (item[1], item[0]))
            ],
            problems=[
                StudentProblemMasteryDTO(problem_id=problem_id, mastery=mastery)
                for problem_id, mastery in sorted(problems.items(), key=lambda item: (item[1], item[0]))
            ],
        )
