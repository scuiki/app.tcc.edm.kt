# ProgSnapAssignmentId é o AssignmentID do dataset, que não se confunde com o id do banco.

from __future__ import annotations

import pytest

from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId


def test_progsnap_assignment_id_wraps_the_dataset_int():
    assert ProgSnapAssignmentId(439).value == 439
    assert str(ProgSnapAssignmentId(439)) == "439"


@pytest.mark.parametrize("not_an_int", [None, "439", 439.0, True])
def test_progsnap_assignment_id_refuses_anything_but_an_int(not_an_int):
    # None viraria "kc/assignment_None/" em silêncio; é a coluna vazia sem importação.
    with pytest.raises(ValueError):
        ProgSnapAssignmentId(not_an_int)


def test_progsnap_assignment_id_is_not_interchangeable_with_a_db_id():
    # O ponto do tipo, comparar com um int tem que dar falso mesmo se os números coincidem.
    progsnap = ProgSnapAssignmentId(1)
    assert progsnap.value == 1
    assert progsnap != 1
