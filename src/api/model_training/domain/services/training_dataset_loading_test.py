# load_training_dataset, o único lugar que monta o recorte do treino e da inferência.

from __future__ import annotations

import pandas as pd
import pytest

from api.assignments.domain.entities.assignment_entity import Assignment
from api.model_training.domain.services.training_dataset_loading import load_training_dataset


class _InMemory:
    def __init__(self, *items) -> None:
        self._by_id = {item.id: item for item in items}

    def get(self, item_id: int):
        return self._by_id.get(item_id)


class _Submissions:
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df
        self.read_with = None

    def list_by_assignment(self, assignment_id: int) -> pd.DataFrame:
        self.read_with = assignment_id
        return self._df


def _events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_type": ["Run.Program", "Compile.Error", "Run.Program"],
            "student_id": ["S1", "S1", "S2"],
        },
        index=[10, 11, 12],
    )


def _load(assignments, cleaned):
    return load_training_dataset(7, assignments, cleaned)


def test_the_dataset_carries_only_program_runs_and_the_ids_callers_need():
    cleaned = _Submissions(_events())
    dataset = _load(
        _InMemory(Assignment(id=7, classroom_id=1, name="A", created_at="t0", progsnap_assignment_id=439)),
        cleaned,
    )

    assert list(dataset.events["event_type"]) == ["Run.Program", "Run.Program"]
    assert list(dataset.events.index) == [0, 1]  # reindexado, quem consome itera por posição
    assert dataset.progsnap_assignment_id.value == 439
    assert (dataset.classroom_id, dataset.assignment_id) == (1, 7)
    assert cleaned.read_with == 7  # pelo id do banco


def test_a_missing_assignment_is_a_named_error():
    with pytest.raises(ValueError, match="assignment"):
        _load(_InMemory(), _Submissions(_events()))
