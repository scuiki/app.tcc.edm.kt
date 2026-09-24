# O pedido e a resposta de POST /classroom-imports/process.

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from api.classroom_import.domain.value_objects.import_report import ClassroomImportReport


class ImportClassroomDatasetDTO(BaseModel):
    classroom_id: int
    raw_dir: Path  # já confinado sob a raiz de dados pelo controller
    main_table: Path  # a MainTable.csv que o professor escolheu


class ImportCheckDTO(BaseModel):
    check: str
    severity: str
    message: str


class AssignmentTrainabilityDTO(BaseModel):
    progsnap_assignment_id: int
    trainable: bool


class ImportClassroomDatasetResponseDTO(BaseModel):
    has_fatal: bool
    checks: list[ImportCheckDTO]
    dataset_summary: dict[str, int]
    per_assignment: list[AssignmentTrainabilityDTO]

    @classmethod
    def from_report(cls, report: ClassroomImportReport) -> "ImportClassroomDatasetResponseDTO":
        return cls(
            has_fatal=report.has_fatal,
            checks=[
                ImportCheckDTO(check=c.check, severity=c.severity, message=c.message)
                for c in report.checks
            ],
            dataset_summary=report.dataset_summary,
            per_assignment=[
                AssignmentTrainabilityDTO(
                    progsnap_assignment_id=a.progsnap_assignment_id, trainable=a.trainable
                )
                for a in report.per_assignment
            ],
        )
