# Valida tudo antes de gravar; grava só sem falha fatal, com a trava de job pega aqui.

from __future__ import annotations

import pandas as pd

from api.assignments.domain.entities.assignment_entity import Assignment, AssignmentStatus
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.classrooms.domain.entities.classroom_entity import Classroom
from api.classrooms.domain.interfaces.classroom_repository import IClassroomRepository
from api.classroom_import.application.dtos.import_classroom_dataset_dto import (
    ImportClassroomDatasetDTO,
    ImportClassroomDatasetResponseDTO,
)
from api.classroom_import.domain.rules.classroom_not_imported_yet_rule import (
    ClassroomNotImportedYetRule,
)
from api.classroom_import.domain.value_objects.import_report import (
    AssignmentTrainability,
    ClassroomImportReport,
    ImportCheck,
)
from api.classroom_import.domain.services.import_summary import summarize_cleaned_submissions
from api.classroom_import.domain.interfaces.progsnap_table_reader import IProgSnapTableReader
from api.classroom_import.domain.services.submission_cleaning import clean_submissions
from api.classroom_import.domain.interfaces.submission_repository import ISubmissionRepository
from api.classroom_import.domain.services.trainability_check import check_assignment_trainability
from api.shared.application.services.clock import utc_now_iso
from api.shared.application.interfaces.job_lock import IJobLock
from api.shared.application.interfaces.unit_of_work import IUnitOfWork
from api.shared.application.use_cases.write_use_case import WriteUseCase
from api.shared.domain.interfaces.business_rule import IBusinessRule

ANOTHER_JOB_RUNNING = ImportCheck(
    check="another_job_running",
    severity="fatal",
    message="Já existe um processamento em andamento. Aguarde a conclusão e tente novamente.",
)


class ImportClassroomDatasetUseCase(WriteUseCase):
    def __init__(
        self,
        classrooms: IClassroomRepository,
        assignments: IAssignmentRepository,
        submissions: ISubmissionRepository,
        unit_of_work: IUnitOfWork,
        job_lock: IJobLock,
        tables: IProgSnapTableReader,
    ) -> None:
        self._classrooms = classrooms
        self._assignments = assignments
        self._submissions = submissions
        self._unit_of_work = unit_of_work
        self._job_lock = job_lock
        self._tables = tables

    def rules(self) -> list[IBusinessRule]:
        return [ClassroomNotImportedYetRule(self._classrooms)]

    def _run(self, dto: ImportClassroomDatasetDTO) -> ImportClassroomDatasetResponseDTO:
        lock = self._job_lock.acquire("classroom_import", job_id=None)
        if not lock:
            report = ClassroomImportReport.nothing_imported([ANOTHER_JOB_RUNNING])
        else:
            with lock:
                report = self._import(dto)
        return ImportClassroomDatasetResponseDTO.from_report(report)

    def _import(self, dto: ImportClassroomDatasetDTO) -> ClassroomImportReport:
        main_table, checks = self._tables.read_main_table(dto.main_table)
        if main_table is None:
            return ClassroomImportReport.nothing_imported(checks)  # falha dura, nada é gravado

        code_by_snapshot = self._tables.read_code_snapshots(dto.raw_dir)
        cleaned, cleaning_checks = clean_submissions(main_table, code_by_snapshot)
        per_assignment, trainability_checks = check_assignment_trainability(cleaned)

        self._save(dto.classroom_name, cleaned, per_assignment)
        return ClassroomImportReport(
            checks=checks + cleaning_checks + trainability_checks,
            dataset_summary=summarize_cleaned_submissions(cleaned),
            per_assignment=per_assignment,
        )

    def _save(
        self,
        classroom_name: str,
        cleaned: pd.DataFrame,
        per_assignment: list[AssignmentTrainability],
    ) -> None:
        # A turma, os assignments e o dado limpo de cada um, tudo ou nada.
        created_at = utc_now_iso()
        trainable = {a.progsnap_assignment_id: a.trainable for a in per_assignment}
        with self._unit_of_work:
            classroom_id = self._classrooms.add(
                Classroom(id=None, name=classroom_name, created_at=created_at)
            )
            for progsnap_id, events in cleaned.groupby("progsnap_assignment_id", sort=True):
                assignment_id = self._assignments.add(
                    Assignment(
                        id=None,
                        classroom_id=classroom_id,
                        name=f"Assignment {int(progsnap_id)}",
                        created_at=created_at,
                        status=(
                            AssignmentStatus.READY_FOR_KC_GENERATION
                            if trainable.get(int(progsnap_id))
                            else AssignmentStatus.STATISTICS_ONLY
                        ),
                        progsnap_assignment_id=int(progsnap_id),
                    )
                )
                self._submissions.add_many(assignment_id, events)
