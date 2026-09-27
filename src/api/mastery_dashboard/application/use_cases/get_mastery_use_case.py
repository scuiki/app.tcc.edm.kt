# O bloco "o que o modelo prevê", conceitos e problemas por domínio previsto, com a distribuição.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.services.existing_assignment import get_existing_assignment
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)
from api.mastery_dashboard.application.dtos.mastery_dashboard_dto import (
    KnowledgeComponentMasteryDTO,
    KnowledgeComponentRefDTO,
    MasteryResponseDTO,
    ProblemMasteryDTO,
    TrainedModelDTO,
)
from api.mastery_dashboard.application.services.concept_bindings import load_concept_bindings
from api.mastery_dashboard.application.services.published_model_mastery import PublishedModelMastery
from api.mastery_dashboard.domain.services.mastery_by_knowledge_component import (
    aggregate_by_knowledge_component,
)
from api.mastery_dashboard.domain.services.mastery_distribution import mean_and_histogram


class GetMasteryUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        knowledge_components: IKnowledgeComponentRepository,
        problem_kcs: IProblemKnowledgeComponentRepository,
        mastery: PublishedModelMastery,
    ) -> None:
        self._assignments = assignments
        self._knowledge_components = knowledge_components
        self._problem_kcs = problem_kcs
        self._mastery = mastery

    def execute(self, assignment_id: int) -> MasteryResponseDTO:
        assignment = get_existing_assignment(self._assignments, assignment_id)
        matrix, model = self._mastery.of(assignment)
        if model is None:
            return MasteryResponseDTO(
                assignment_id=assignment_id, model=None, knowledge_components=[], problems=[]
            )
        concepts = load_concept_bindings(assignment_id, self._knowledge_components, self._problem_kcs)

        by_kc: dict[int, list[float]] = {}
        for (_student_id, kc_id), mastery in aggregate_by_knowledge_component(
            matrix, concepts.kcs_by_problem
        ).items():
            by_kc.setdefault(kc_id, []).append(mastery)
        by_problem: dict[int, list[float]] = {}
        for (_student_id, problem_id), mastery in matrix.items():
            by_problem.setdefault(problem_id, []).append(mastery)

        knowledge_components = []
        for kc_id, values in by_kc.items():
            mean, histogram = mean_and_histogram(values)
            knowledge_components.append(
                KnowledgeComponentMasteryDTO(
                    kc_id=kc_id,
                    kc_name=concepts.name_of(kc_id),
                    problem_ids=concepts.problems_by_kc.get(kc_id, []),
                    mean_mastery=mean,
                    histogram=histogram,
                )
            )
        problems = []
        for problem_id, values in by_problem.items():
            mean, histogram = mean_and_histogram(values)
            problems.append(
                ProblemMasteryDTO(
                    problem_id=problem_id,
                    mean_mastery=mean,
                    histogram=histogram,
                    kcs=[
                        KnowledgeComponentRefDTO(kc_id=kc_id, kc_name=concepts.name_of(kc_id))
                        for kc_id in concepts.kcs_by_problem.get(problem_id, [])
                    ],
                )
            )
        return MasteryResponseDTO(
            assignment_id=assignment_id,
            model=TrainedModelDTO(
                version_number=model.version_number,
                trained_at=model.created_at,
                student_count=len({student_id for student_id, _ in matrix}),
                problem_count=len(by_problem),
                knowledge_component_count=len(by_kc),
            ),
            knowledge_components=sorted(
                knowledge_components, key=lambda kc: (kc.mean_mastery, kc.kc_id)
            ),
            problems=sorted(problems, key=lambda p: (p.mean_mastery, p.problem_id)),
        )
