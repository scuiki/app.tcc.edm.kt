# O professor cria uma turma só com o nome, antes de enviar qualquer dado.

from __future__ import annotations

from api.classrooms.application.dtos.edit_classrooms_dto import ClassroomDTO, CreateClassroomDTO
from api.classrooms.domain.entities.classroom_entity import Classroom
from api.classrooms.domain.interfaces.classroom_repository import IClassroomRepository
from api.classrooms.domain.rules.classroom_name_is_available_rule import (
    ClassroomNameIsAvailableRule,
)
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.services.clock import utc_now_iso
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.interfaces.business_rule import IBusinessRule


class CreateClassroomUseCase(WriteUseCase):
    def __init__(self, classrooms: IClassroomRepository, unit_of_work: IUnitOfWork) -> None:
        self._classrooms = classrooms
        self._unit_of_work = unit_of_work

    def rules(self) -> list[IBusinessRule]:
        return [ClassroomNameIsAvailableRule(self._classrooms)]

    def _run(self, dto: CreateClassroomDTO) -> ClassroomDTO:
        created_at = utc_now_iso()
        with self._unit_of_work:
            classroom_id = self._classrooms.add(
                Classroom(id=None, name=dto.name, created_at=created_at)
            )
        return ClassroomDTO(id=classroom_id, name=dto.name, created_at=created_at)
