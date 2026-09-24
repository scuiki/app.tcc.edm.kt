"""Importa a MainTable escolhida: valida, limpa, checa a treinabilidade e grava tudo junto.

Validar tudo, depois gravar: o pré-voo inteiro roda sem tocar o banco nem o disco, e só sem
nenhuma checagem fatal a gravação acontece. A trava de job é pega AQUI e não no upload, porque
ela protege o estado compartilhado (banco e data/), que só é tocado na gravação.
"""

from __future__ import annotations

import pandas as pd

from api.assignments.domain.assignment_entity import Assignment, AssignmentStatus
from api.assignments.domain.assignment_repository import AssignmentRepository
from api.assignments.domain.classroom_entity import Classroom
from api.assignments.domain.classroom_repository import ClassroomRepository
from api.assignments.domain.classroom_slug import ClassroomSlug
from api.classroom_import.application.import_classroom_dataset_dto import (
    ImportClassroomDatasetDTO,
    ImportClassroomDatasetResponseDTO,
)
from api.classroom_import.domain.classroom_not_imported_yet_rule import ClassroomNotImportedYetRule
from api.classroom_import.domain.cleaned_submissions_store import CleanedSubmissionsStore
from api.classroom_import.domain.import_report import (
    AssignmentTrainability,
    ClassroomImportReport,
    ImportCheck,
)
from api.classroom_import.domain.import_summary import summarize_cleaned_submissions
from api.classroom_import.domain.progsnap_upload import ProgSnapTableReader
from api.classroom_import.domain.submission_cleaning import clean_submissions
from api.classroom_import.domain.submission_entity import Submission
from api.classroom_import.domain.submission_repository import SubmissionRepository
from api.classroom_import.domain.trainability_check import check_assignment_trainability
from api.shared.application.clock import utc_now_iso
from api.shared.application.job_lock import JobLock
from api.shared.application.unit_of_work import UnitOfWork
from api.shared.application.write_use_case import WriteUseCase
from api.shared.domain.business_rule import BusinessRule

ANOTHER_JOB_RUNNING = ImportCheck(
    check="another_job_running",
    severity="fatal",
    message="Já existe um processamento em andamento. Aguarde a conclusão e tente novamente.",
)


class ImportClassroomDatasetUseCase(WriteUseCase):
    def __init__(
        self,
        classrooms: ClassroomRepository,
        assignments: AssignmentRepository,
        submissions: SubmissionRepository,
        unit_of_work: UnitOfWork,
        job_lock: JobLock,
        tables: ProgSnapTableReader,
        cleaned_submissions: CleanedSubmissionsStore,
    ) -> None:
        self._classrooms = classrooms
        self._assignments = assignments
        self._submissions = submissions
        self._unit_of_work = unit_of_work
        self._job_lock = job_lock
        self._tables = tables
        self._cleaned_submissions = cleaned_submissions

    def rules(self) -> list[BusinessRule]:
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
            return ClassroomImportReport.nothing_imported(checks)  # falha dura: nada é gravado

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
        """Parquet em `.tmp` → INSERTs numa transação → publica os Parquet só depois do COMMIT."""
        created_at = utc_now_iso()
        trainable = {a.progsnap_assignment_id: a.trainable for a in per_assignment}
        staged = self._cleaned_submissions.stage(ClassroomSlug.from_name(classroom_name), cleaned)
        try:
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
                    for event in events.itertuples(index=False):
                        self._submissions.add(_submission(assignment_id, event, created_at))
        except BaseException:
            staged.discard()
            raise
        staged.publish()


def _submission(assignment_id: int, event, created_at: str) -> Submission:
    # O score cru e contínuo; nunca o binário e nunca o código (o snapshot fica só no Parquet).
    return Submission(
        id=None,
        assignment_id=assignment_id,
        code_snapshot_id=str(event.code_snapshot_id),
        student_id=None if pd.isna(event.student_id) else str(event.student_id),
        problem_id=None if pd.isna(event.problem_id) else int(event.problem_id),
        score=None if pd.isna(event.score) else float(event.score),
        created_at=created_at,
        event_type=str(event.event_type),
    )
