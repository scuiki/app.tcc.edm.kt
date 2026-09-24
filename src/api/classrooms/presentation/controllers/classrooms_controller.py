# As rotas de /classrooms, o CRUD das turmas do professor.

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.classroom_import.application.dtos.list_classrooms_dto import ListClassroomsResponseDTO
from api.classroom_import.application.use_cases.list_classrooms_use_case import (
    ListClassroomsUseCase,
)
from api.classrooms.application.dtos.edit_classrooms_dto import (
    ClassroomDTO,
    CreateClassroomDTO,
    RemoveClassroomDTO,
    RemovedClassroomDTO,
    RenameClassroomBody,
    RenameClassroomDTO,
)
from api.classrooms.application.use_cases.create_classroom_use_case import CreateClassroomUseCase
from api.classrooms.application.use_cases.remove_classroom_use_case import RemoveClassroomUseCase
from api.classrooms.application.use_cases.rename_classroom_use_case import RenameClassroomUseCase
from api.classrooms.presentation import dependencies

router = APIRouter(prefix="/classrooms", tags=["classrooms"])


@router.get(
    "",
    response_model=ListClassroomsResponseDTO,
    description="As turmas ativas, com o número de problemas e de alunos e a situação de cada uma.",
)
def list_classrooms(
    use_case: ListClassroomsUseCase = Depends(dependencies.list_classrooms_use_case),
) -> ListClassroomsResponseDTO:
    return use_case.execute()


@router.post(
    "",
    status_code=201,
    response_model=ClassroomDTO,
    description="Cria uma turma só com o nome; um nome já usado por outra turma ativa dá 409.",
)
def create_classroom(
    body: CreateClassroomDTO,
    use_case: CreateClassroomUseCase = Depends(dependencies.create_classroom_use_case),
) -> ClassroomDTO:
    return use_case.execute(body)


@router.put(
    "/{classroom_id}",
    response_model=ClassroomDTO,
    description="Renomeia a turma, com a mesma regra de nome único.",
)
def rename_classroom(
    classroom_id: int,
    body: RenameClassroomBody,
    use_case: RenameClassroomUseCase = Depends(dependencies.rename_classroom_use_case),
) -> ClassroomDTO:
    return use_case.execute(RenameClassroomDTO(classroom_id=classroom_id, name=body.name))


@router.delete(
    "/{classroom_id}",
    response_model=RemovedClassroomDTO,
    description="Exclui a turma e os assignments dela; nada é apagado do banco nem do disco.",
)
def remove_classroom(
    classroom_id: int,
    use_case: RemoveClassroomUseCase = Depends(dependencies.remove_classroom_use_case),
) -> RemovedClassroomDTO:
    return use_case.execute(RemoveClassroomDTO(classroom_id=classroom_id))
