# Dado limpo do assignment, só Run.Program; montado por load_training_dataset, único ponto do corte

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId


@dataclass(frozen=True)
class TrainingDataset:
    events: pd.DataFrame  # só Run.Program
    progsnap_assignment_id: ProgSnapAssignmentId
    classroom_id: int
    assignment_id: int  # com o classroom_id, é o endereço dos arquivos do treino em data/
