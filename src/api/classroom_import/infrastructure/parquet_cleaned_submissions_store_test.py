"""ParquetCleanedSubmissionsStore: gravar em dois tempos nunca destrói o dado que já estava lá."""

from __future__ import annotations

import pandas as pd
import pytest

from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId
from api.classroom_import.domain.submission_cleaning import CLEANED_COLUMNS
from api.classroom_import.infrastructure.parquet_cleaned_submissions_store import (
    ParquetCleanedSubmissionsStore,
)

SLUG = ClassroomSlug("turma-x")

pytestmark = pytest.mark.usefixtures("data_root")



def test_nothing_is_visible_until_publish(a439_mini, data_root):
    store = ParquetCleanedSubmissionsStore()

    staged = store.stage(SLUG, a439_mini)

    assert not store.exists(SLUG, ProgSnapAssignmentId(439))
    staged.publish()
    assert store.exists(SLUG, ProgSnapAssignmentId(439))


def test_read_returns_what_was_published(a439_mini):
    store = ParquetCleanedSubmissionsStore()
    store.stage(SLUG, a439_mini).publish()

    back = store.read(SLUG, ProgSnapAssignmentId(439))

    pd.testing.assert_frame_equal(
        back, a439_mini[CLEANED_COLUMNS].reset_index(drop=True), check_dtype=False
    )


def test_discarding_a_failed_rewrite_keeps_the_previous_file(a439_mini, data_root):
    # `to_parquet` sobrescreve: gravar direto no destino destruiria o arquivo bom antes de saber
    # se a transação passa. O staging em .tmp é o que torna a falha não destrutiva.
    store = ParquetCleanedSubmissionsStore()
    store.stage(SLUG, a439_mini).publish()
    path = data_root / "turma-x" / "clean" / "assignment_439.parquet"
    original = path.read_bytes()

    store.stage(SLUG, a439_mini.head(2)).discard()

    assert path.read_bytes() == original
    assert not list(path.parent.glob("*.tmp")), "restou temporário da gravação interrompida"
