# Em que ClassroomStatus uma turma está, a partir do que os assignments dela já têm.

from __future__ import annotations

from api.classrooms.domain.value_objects.classroom_status import ClassroomStatus


def classify_classroom_status(problem_count: int, has_published_model: bool) -> ClassroomStatus:
    if problem_count == 0:
        return ClassroomStatus.AWAITING_DATA
    if has_published_model:
        return ClassroomStatus.TRAINED
    return ClassroomStatus.IN_PROGRESS
