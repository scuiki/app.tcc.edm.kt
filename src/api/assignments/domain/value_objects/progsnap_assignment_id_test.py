"""ProgSnapAssignmentId: o AssignmentID do dataset, que não se confunde com o id do banco."""

from __future__ import annotations

import pytest

from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId


def test_progsnap_assignment_id_wraps_the_dataset_int():
    assert ProgSnapAssignmentId(439).value == 439
    assert str(ProgSnapAssignmentId(439)) == "439"


@pytest.mark.parametrize("not_an_int", [None, "439", 439.0, True])
def test_progsnap_assignment_id_refuses_anything_but_an_int(not_an_int):
    # None viraria "assignment_None.parquet" em silêncio; é a coluna vazia de um assignment
    # que não veio da importação.
    with pytest.raises(ValueError):
        ProgSnapAssignmentId(not_an_int)


def test_progsnap_assignment_id_is_not_interchangeable_with_a_db_id():
    # O ponto do tipo: assignment.id == 1 e o ProgSnap2 AssignmentID == 439 são ambos int
    # e significam coisas diferentes. Comparar um com o outro tem de ser falso, não acidentalmente
    # verdadeiro quando os números coincidem.
    progsnap = ProgSnapAssignmentId(1)
    assert progsnap.value == 1
    assert progsnap != 1


# --- consolidação: as definições locais somem ----------------------------------------------
