"""Contrato de saída estruturado da ingestão por severidade.

Testes puros (sem I/O, sem SQLite, sem GPU): asseguram invariantes do contrato — has_fatal
deriva da presença de ≥1 item fatal, ImportCheck é write-once (frozen), e o ClassroomImportReport
preserva per_assignment. Nada de valores mágicos de AUC.
"""

from __future__ import annotations

import dataclasses

import pytest

from api.classroom_import.domain.value_objects.import_report import (
    AssignmentTrainability,
    ClassroomImportReport,
    ImportCheck,
)


def _empty_report(items) -> ClassroomImportReport:
    return ClassroomImportReport(checks=items, dataset_summary={}, per_assignment=[])


def test_has_fatal_true_when_any_fatal_item():
    report = _empty_report([ImportCheck(check="missing_column", severity="fatal", message="msg")])
    assert report.has_fatal is True


def test_has_fatal_false_with_only_warning_and_viability():
    report = _empty_report(
        [
            ImportCheck(check="encoding", severity="warning", message="BOM"),
            ImportCheck(check="small_cohort", severity="viability", message="poucos alunos"),
        ]
    )
    assert report.has_fatal is False


def test_has_fatal_false_when_empty():
    assert _empty_report([]).has_fatal is False


def test_report_item_is_frozen():
    item = ImportCheck(check="orphan", severity="warning", message="x", count=3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.severity = "fatal"  # type: ignore[misc]


def test_ingest_report_preserves_per_assignment():
    summary = AssignmentTrainability(
        progsnap_assignment_id=439,
        n_students_eligible=300,
        n_problems=10,
        n_submissions=1200,
        both_classes_present=True,
        trainable=True,
    )
    report = ClassroomImportReport(
        checks=[],
        dataset_summary={"n_students": 300, "n_assignments": 1},
        per_assignment=[summary],
    )
    assert report.per_assignment[0].trainable is True
    assert report.per_assignment[0].reasons == []
    assert report.dataset_summary["n_assignments"] == 1
