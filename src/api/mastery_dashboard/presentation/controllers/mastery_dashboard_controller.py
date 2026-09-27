# As rotas de /mastery-dashboard são HTTP puro e só leitura; a única escrita é a matriz, uma vez.

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.mastery_dashboard.application.use_cases.get_mastery_use_case import GetMasteryUseCase
from api.mastery_dashboard.application.use_cases.get_student_use_case import GetStudentUseCase
from api.mastery_dashboard.application.use_cases.get_submission_statistics_use_case import (
    GetSubmissionStatisticsUseCase,
)
from api.mastery_dashboard.application.use_cases.list_students_use_case import ListStudentsUseCase
from api.mastery_dashboard.application.dtos.mastery_dashboard_dto import (
    ListStudentsResponseDTO,
    MasteryResponseDTO,
    StudentDetailDTO,
    SubmissionStatisticsResponseDTO,
)
from api.mastery_dashboard.presentation import dependencies

router = APIRouter(prefix="/mastery-dashboard/{assignment_id}", tags=["mastery_dashboard"])


@router.get("/submission-statistics", response_model=SubmissionStatisticsResponseDTO)
def get_submission_statistics(
    assignment_id: int,
    use_case: GetSubmissionStatisticsUseCase = Depends(
        dependencies.get_submission_statistics_use_case
    ),
) -> SubmissionStatisticsResponseDTO:
    return use_case.execute(assignment_id)


@router.get("/mastery", response_model=MasteryResponseDTO)
def get_mastery(
    assignment_id: int,
    use_case: GetMasteryUseCase = Depends(dependencies.get_mastery_use_case),
) -> MasteryResponseDTO:
    return use_case.execute(assignment_id)


@router.get("/students", response_model=ListStudentsResponseDTO)
def list_students(
    assignment_id: int,
    use_case: ListStudentsUseCase = Depends(dependencies.list_students_use_case),
) -> ListStudentsResponseDTO:
    return use_case.execute(assignment_id)


@router.get("/students/{student_id}", response_model=StudentDetailDTO)
def get_student(
    assignment_id: int,
    student_id: str,
    use_case: GetStudentUseCase = Depends(dependencies.get_student_use_case),
) -> StudentDetailDTO:
    return use_case.execute(assignment_id, student_id)
