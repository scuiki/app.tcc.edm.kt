# A origem do conceito, com o enunciado, as justificativas, o trecho e as soluções de cada problema.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.problems.domain.interfaces.problem_repository import IProblemRepository
from api.classroom_import.domain.interfaces.submission_repository import ISubmissionRepository
from api.knowledge_components.application.dtos.get_knowledge_component_origin_dto import (
    KnowledgeComponentEvidenceDTO,
    KnowledgeComponentOriginDTO,
    ProblemOriginDTO,
    SampledSolutionDTO,
)
from api.knowledge_components.domain.entities.sampled_solution_entity import SampledSolution
from api.knowledge_components.domain.interfaces.candidate_knowledge_component_repository import (
    ICandidateKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.knowledge_component_evidence_repository import (
    IKnowledgeComponentEvidenceRepository,
)
from api.knowledge_components.domain.interfaces.knowledge_component_repository import (
    IKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.problem_knowledge_component_repository import (
    IProblemKnowledgeComponentRepository,
)
from api.knowledge_components.domain.interfaces.sampled_solution_repository import (
    ISampledSolutionRepository,
)
from api.knowledge_components.domain.services.active_knowledge_component import (
    get_active_knowledge_component,
)


# O par sem KC candidato é o vínculo do professor, e o par com candidato e sem trecho foi descartado
class GetKnowledgeComponentOriginUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        problems: IProblemRepository,
        knowledge_components: IKnowledgeComponentRepository,
        problem_kcs: IProblemKnowledgeComponentRepository,
        candidate_kcs: ICandidateKnowledgeComponentRepository,
        evidence: IKnowledgeComponentEvidenceRepository,
        sampled_solutions: ISampledSolutionRepository,
        submissions: ISubmissionRepository,
    ) -> None:
        self._assignments = assignments
        self._problems = problems
        self._knowledge_components = knowledge_components
        self._problem_kcs = problem_kcs
        self._candidate_kcs = candidate_kcs
        self._evidence = evidence
        self._sampled_solutions = sampled_solutions
        self._submissions = submissions

    def execute(self, kc_id: int) -> KnowledgeComponentOriginDTO:
        knowledge_component = get_active_knowledge_component(
            self._knowledge_components, self._assignments, kc_id
        )
        assignment_id = knowledge_component.assignment_id
        problem_ids = sorted(self._problem_kcs.problems_of(kc_id))
        statement_of = {
            problem.problem_id: problem.statement
            for problem in self._problems.list_by_assignment(assignment_id)
        }
        reasonings_of: dict[int, list[str]] = {}
        candidates = self._candidate_kcs.list_by_assignment(assignment_id)
        for candidate in sorted(candidates, key=lambda c: c.position):
            # A justificativa sem tradução sai, porque a resposta não aceita texto nulo
            if candidate.kc_id == kc_id and candidate.translated_reasoning is not None:
                reasonings_of.setdefault(candidate.problem_id, []).append(
                    candidate.translated_reasoning
                )
        evidence_of = {
            evidence.problem_id: KnowledgeComponentEvidenceDTO(
                position=evidence.position,
                first_line=evidence.first_line,
                last_line=evidence.last_line,
            )
            for evidence in self._evidence.list_by_assignment(assignment_id)
            if evidence.kc_id == kc_id
        }
        solutions_of: dict[int, list[SampledSolution]] = {}
        solutions = self._sampled_solutions.list_by_assignment(assignment_id)
        for solution in sorted(solutions, key=lambda s: s.position):
            if solution.problem_id in problem_ids:
                solutions_of.setdefault(solution.problem_id, []).append(solution)
        code_of = self._submissions.get_codes(
            [solution.submission_id for group in solutions_of.values() for solution in group]
        )
        return KnowledgeComponentOriginDTO(
            kc_id=kc_id,
            name=knowledge_component.name,
            is_generated_by_llm=knowledge_component.is_generated_by_llm,
            problems=[
                ProblemOriginDTO(
                    problem_id=problem_id,
                    statement=statement_of[problem_id],
                    translated_reasonings=reasonings_of.get(problem_id, []),
                    evidence=evidence_of.get(problem_id),
                    sampled_solutions=[
                        SampledSolutionDTO(
                            position=solution.position, code=code_of[solution.submission_id]
                        )
                        for solution in solutions_of.get(problem_id, [])
                    ],
                )
                for problem_id in problem_ids
            ],
        )
