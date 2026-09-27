# As respostas de /mastery-dashboard/{assignment_id}/...

from __future__ import annotations

from pydantic import BaseModel


class KnowledgeComponentRefDTO(BaseModel):
    kc_id: int
    kc_name: str


# O bloco "o que aconteceu", contado das execuções, sem modelo


class ProblemStatisticsDTO(BaseModel):
    problem_id: int
    success_rate: float
    median_attempts_to_complete: float | None  # None quando ninguém completou
    students_attempted: int
    students_completed: int
    compile_errors_per_run: float
    kcs: list[KnowledgeComponentRefDTO]  # vazio sem conceitos aprovados


class KnowledgeComponentStatisticsDTO(BaseModel):
    kc_id: int
    kc_name: str
    problem_ids: list[int]
    success_rate: float
    runs: int


class SubmissionStatisticsResponseDTO(BaseModel):
    assignment_id: int
    student_count: int
    problems: list[ProblemStatisticsDTO]  # da menor taxa de acerto para a maior
    knowledge_components: list[KnowledgeComponentStatisticsDTO]  # idem; vazio até aprovar


# O bloco "o que o modelo prevê", só com modelo publicado


class TrainedModelDTO(BaseModel):
    version_number: int
    trained_at: str
    student_count: int
    problem_count: int
    knowledge_component_count: int


class KnowledgeComponentMasteryDTO(BaseModel):
    kc_id: int
    kc_name: str
    problem_ids: list[int]
    mean_mastery: float
    histogram: list[int]  # alunos por faixa de 10 pontos, de 0 a 100%


class ProblemMasteryDTO(BaseModel):
    problem_id: int
    mean_mastery: float
    histogram: list[int]
    kcs: list[KnowledgeComponentRefDTO]


class MasteryResponseDTO(BaseModel):
    assignment_id: int
    model: TrainedModelDTO | None  # None sem modelo publicado, e as listas vêm vazias
    knowledge_components: list[KnowledgeComponentMasteryDTO]  # da menor média para a maior
    problems: list[ProblemMasteryDTO]  # idem


class StudentKnowledgeComponentMasteryDTO(BaseModel):
    kc_id: int
    kc_name: str
    mastery: float


class StudentSummaryDTO(BaseModel):
    student_id: str
    mean_mastery: float  # média dos problemas do exercício
    completed: int
    attempted: int
    weakest_kcs: list[StudentKnowledgeComponentMasteryDTO]  # os três de menor domínio


class ListStudentsResponseDTO(BaseModel):
    assignment_id: int
    students: list[StudentSummaryDTO]  # da menor média para a maior; vazio sem modelo


class StudentProblemMasteryDTO(BaseModel):
    problem_id: int
    mastery: float


class StudentDetailDTO(BaseModel):
    student_id: str
    mean_mastery: float
    completed: int
    attempted: int
    runs: int
    compile_errors: int
    knowledge_components: list[StudentKnowledgeComponentMasteryDTO]  # do menor domínio para o maior
    problems: list[StudentProblemMasteryDTO]  # idem
