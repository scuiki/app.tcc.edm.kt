"""CleanedSubmissionsStore em Parquet: data/<turma>/clean/assignment_<N>.parquet.

O disco não participa da transação do SQLite, então gravar é em dois tempos. `stage` escreve cada
arquivo como `.tmp`; o use case faz os INSERTs na transação e só depois do COMMIT chama `publish`,
que renomeia os `.tmp` para o lugar (rename é atômico por arquivo). Se a transação falhar,
`discard` apaga os temporários e o Parquet anterior segue intacto: nenhum caminho de falha destrói
dado. Uma queda entre o COMMIT e o rename deixa o banco novo com o Parquet antigo: inconsistente,
mas não destrutivo, e uma reimportação reconstrói.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from api.assignments.domain.classroom_slug import ClassroomSlug
from api.assignments.domain.progsnap_assignment_id import ProgSnapAssignmentId
from api.classroom_import.domain.submission_cleaning import CLEANED_COLUMNS
from api.shared.infrastructure import data_layout


class _StagedParquetFiles:
    def __init__(self, staged: list[tuple[Path, Path]]) -> None:
        self._staged = staged  # (temporário, destino final)

    def publish(self) -> None:
        for tmp_path, destination in self._staged:
            tmp_path.replace(destination)

    def discard(self) -> None:
        for tmp_path, _destination in self._staged:
            tmp_path.unlink(missing_ok=True)


class ParquetCleanedSubmissionsStore:
    def stage(self, classroom_slug: ClassroomSlug, cleaned: pd.DataFrame) -> _StagedParquetFiles:
        """Escreve um `.tmp` por assignment; o destino final só é tocado no `publish`."""
        data_layout.cleaned_submissions_dir(classroom_slug).mkdir(parents=True, exist_ok=True)
        staged: list[tuple[Path, Path]] = []
        try:
            for progsnap_id, group in cleaned.groupby("progsnap_assignment_id", sort=True):
                destination = data_layout.cleaned_submissions_path(classroom_slug, int(progsnap_id))
                tmp_path = destination.with_suffix(".parquet.tmp")
                group[CLEANED_COLUMNS].to_parquet(tmp_path, engine="pyarrow", index=False)
                staged.append((tmp_path, destination))
        except BaseException:
            _StagedParquetFiles(staged).discard()
            raise
        return _StagedParquetFiles(staged)

    def read(
        self, classroom_slug: ClassroomSlug, progsnap_assignment_id: ProgSnapAssignmentId
    ) -> pd.DataFrame:
        path = data_layout.cleaned_submissions_path(classroom_slug, progsnap_assignment_id)
        return pd.read_parquet(path, engine="pyarrow")

    def exists(
        self, classroom_slug: ClassroomSlug, progsnap_assignment_id: ProgSnapAssignmentId
    ) -> bool:
        return data_layout.cleaned_submissions_path(classroom_slug, progsnap_assignment_id).exists()
