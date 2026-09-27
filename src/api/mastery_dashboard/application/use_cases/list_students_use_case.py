# A lista de alunos, leve e inteira; o professor ordena no front e abre o detalhe ao clicar.

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
    ListStudentsResponseDTO,
    StudentKnowledgeComponentMasteryDTO,
    StudentSummaryDTO,
)
from api.mastery_dashboard.application.services.concept_bindings import load_concept_bindings
from api.mastery_dashboard.application.services.published_model_mastery import PublishedModelMastery
from api.mastery_dashboard.domain.services.mastery_by_knowledge_component import (
    aggregate_by_knowledge_component,
)
from api.mastery_dashboard.domain.services.student_mastery import (
    mean_mastery_by_student,
    weakest_knowledge_components,
)
from api.mastery_dashboard.domain.services.submission_statistics_calculation import (
    compute_student_activity,
)


class ListStudentsUseCase:
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

    def execute(self, assignment_id: int) -> ListStudentsResponseDTO:
        assignment = get_existing_assignment(self._assignments, assignment_id)
        matrix, model = self._mastery.of(assignment)
        if model is None:
            return ListStudentsResponseDTO(assignment_id=assignment_id, students=[])
        concepts = load_concept_bindings(assignment_id, self._knowledge_components, self._problem_kcs)
        activity = compute_student_activity(self._submissions.list_by_assignment(assignment_id))

        by_student_kc: dict[str, dict[int, float]] = {}
        for (student_id, kc_id), mastery in aggregate_by_knowledge_component(
            matrix, concepts.kcs_by_problem
        ).items():
            by_student_kc.setdefault(student_id, {})[kc_id] = mastery

        students = []
        for student_id, mean in mean_mastery_by_student(matrix).items():
            done = activity.get(student_id)
            students.append(
                StudentSummaryDTO(
                    student_id=student_id,
                    mean_mastery=mean,
                    completed=done.completed if done else 0,
                    attempted=done.attempted if done else 0,
                    weakest_kcs=[
                        StudentKnowledgeComponentMasteryDTO(
                            kc_id=kc_id, kc_name=concepts.name_of(kc_id), mastery=mastery
                        )
                        for kc_id, mastery in weakest_knowledge_components(
                            by_student_kc.get(student_id, {})
                        )
                    ],
                )
            )
        return ListStudentsResponseDTO(
            assignment_id=assignment_id,
            students=sorted(students, key=lambda s: (s.mean_mastery, s.student_id)),
        )
