# Dado limpo do assignment, só Run.Program; montado por load_training_dataset, único ponto do corte

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId


@dataclass(frozen=True)
class TrainingDataset:
    events: pd.DataFrame  # só Run.Program
    classroom_slug: ClassroomSlug
    progsnap_assignment_id: ProgSnapAssignmentId
    classroom_id: int
