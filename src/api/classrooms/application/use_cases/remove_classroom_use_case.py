# O professor exclui uma turma, e os assignments dela saem junto; tudo fica como histórico.

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.classrooms.application.dtos.edit_classrooms_dto import (
    RemoveClassroomDTO,
    RemovedClassroomDTO,
)
from api.classrooms.domain.interfaces.classroom_repository import IClassroomRepository
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.services.clock import utc_now_iso
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.errors.not_found import NotFound


class RemoveClassroomUseCase(WriteUseCase):
    def __init__(
        self,
        classrooms: IClassroomRepository,
        assignments: IAssignmentRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._classrooms = classrooms
        self._assignments = assignments
        self._unit_of_work = unit_of_work

    def _run(self, dto: RemoveClassroomDTO) -> RemovedClassroomDTO:
        if self._classrooms.get(dto.classroom_id) is None:
            raise NotFound("turma inexistente")
        # KCs, problemas, tentativas e modelos só são alcançados pelo assignment, e ficam intocados
        removed_at = utc_now_iso()
        with self._unit_of_work:
            self._assignments.remove_all_of_classroom(dto.classroom_id, removed_at)
            self._classrooms.remove(dto.classroom_id, removed_at)
        return RemovedClassroomDTO(deleted_classroom_id=dto.classroom_id)
