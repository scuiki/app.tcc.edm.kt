# Os três estados da turma e a ordem em que são decididos.

from __future__ import annotations

from api.classrooms.domain.services.classroom_status_classification import (
    classify_classroom_status,
)
from api.classrooms.domain.value_objects.classroom_status import ClassroomStatus


def test_a_classroom_without_problems_is_awaiting_data():
    assert classify_classroom_status(0, has_published_model=False) is ClassroomStatus.AWAITING_DATA


def test_a_classroom_with_data_and_no_model_is_in_progress():
    assert classify_classroom_status(10, has_published_model=False) is ClassroomStatus.IN_PROGRESS


def test_one_published_model_is_enough_to_be_trained():
    assert classify_classroom_status(10, has_published_model=True) is ClassroomStatus.TRAINED
