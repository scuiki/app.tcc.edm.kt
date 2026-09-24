"""O dado que treino e inferência consomem: o dado limpo do assignment, só com Run.Program.

Quem monta é `services/training_dataset_loading.py`, o único lugar que faz esse recorte.
"""

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
