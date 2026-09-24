# O professor renomeia uma turma; os arquivos dela estão no id, então nada muda no disco.

from __future__ import annotations

from api.classrooms.application.dtos.edit_classrooms_dto import ClassroomDTO, RenameClassroomDTO
from api.classrooms.domain.interfaces.classroom_repository import IClassroomRepository
from api.classrooms.domain.rules.classroom_name_is_available_rule import (
    ClassroomNameIsAvailableRule,
)
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.errors.not_found import NotFound
from api.shared.domain.interfaces.business_rule import IBusinessRule


class RenameClassroomUseCase(WriteUseCase):
    def __init__(self, classrooms: IClassroomRepository, unit_of_work: IUnitOfWork) -> None:
        self._classrooms = classrooms
        self._unit_of_work = unit_of_work

    def rules(self) -> list[IBusinessRule]:
        return [ClassroomNameIsAvailableRule(self._classrooms)]

    def execute(self, dto: RenameClassroomDTO) -> ClassroomDTO:
        if self._classrooms.get(dto.classroom_id) is None:
            raise NotFound("turma inexistente")
        return super().execute(dto)

    def _run(self, dto: RenameClassroomDTO) -> ClassroomDTO:
        with self._unit_of_work:
            self._classrooms.rename(dto.classroom_id, dto.name)
        classroom = self._classrooms.get(dto.classroom_id)
        return ClassroomDTO(id=classroom.id, name=classroom.name, created_at=classroom.created_at)
