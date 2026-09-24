# Pré-voo de falhas duras; fatal devolve None sem gravar, sem mensagem com bytes do aluno.

from __future__ import annotations

from pathlib import Path

import pandas as pd

from api.classroom_import.domain.value_objects.import_report import ImportCheck
from api.classroom_import.infrastructure.implementations.progsnap_zip_extractor import (
    find_code_snapshots_file,
)

# Obrigatórias desta ferramenta, além do padrão; sem elas não dá pra rotular first-attempts.
_REQUIRED_COLUMNS = (
    "SubjectID",
    "AssignmentID",
    "ProblemID",
    "CodeStateID",
    "EventType",
    "Score",
    "ServerTimestamp",
)


def read_main_table(main_path: Path) -> tuple[pd.DataFrame | None, list[ImportCheck]]:
    checks: list[ImportCheck] = []

    try:
        # utf-8-sig consome o BOM; detecção heurística de encoding seria dependência extra num v1.
        df = pd.read_csv(main_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        # Não interpolar o detalhe do erro, pode carregar bytes do código do aluno.
        checks.append(
            ImportCheck(
                check="encoding",
                severity="fatal",
                message="arquivo não pôde ser decodificado como UTF-8.",
                location=Path(main_path).name,
            )
        )
        return None, checks

    missing = [col for col in _REQUIRED_COLUMNS if col not in df.columns]
    for col in missing:
        checks.append(
            ImportCheck(
                check="missing_required_column",
                severity="fatal",
                message=f"coluna obrigatória ausente: {col}.",
                location=f"{Path(main_path).name}:{col}",
            )
        )

    if any(c.severity == "fatal" for c in checks):
        # Qualquer falha dura, nada a devolver; a importação aborta sem gravar.
        return None, checks

    # A mesma coerção de tipos do TCC 1; valor inválido vira NaN/NA em vez de explodir.
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True, errors="coerce")
    df["AssignmentID"] = pd.to_numeric(df["AssignmentID"], errors="coerce").astype("Int64")
    df["ProblemID"] = pd.to_numeric(df["ProblemID"], errors="coerce").astype("Int64")

    # Score sai como string no CSV real; sem coagir aqui, a binarização zera em silêncio.
    n_before_nan = int(df["Score"].isna().sum())
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
    n_coerce_failed = int(df["Score"].isna().sum()) - n_before_nan
    if n_coerce_failed > 0:
        # Graduado, não fatal; NaN vira null no persist (pd.isna) e fica fora da binarização.
        checks.append(
            ImportCheck(
                check="score_coercion",
                severity="warning",
                message=f"{n_coerce_failed} valor(es) de Score não numérico(s) coagido(s) a vazio.",
                count=n_coerce_failed,
            )
        )

    return df, checks


def read_code_snapshots(raw_dir: Path) -> dict[str, str]:
    # `{CodeStateID: código Java}`; sem CodeStates no upload, um dict vazio (tudo órfão, aviso).
    path = find_code_snapshots_file(Path(raw_dir))
    if path is None:
        return {}
    table = pd.read_csv(path, encoding="utf-8-sig")
    return dict(zip(table["CodeStateID"].astype(str), table["Code"].fillna("")))


# IProgSnapTableReader sobre os CSVs do upload.
class ProgSnapCsvReader:
    def read_main_table(self, path: Path) -> tuple[pd.DataFrame | None, list[ImportCheck]]:
        return read_main_table(path)

    def read_code_snapshots(self, raw_dir: Path) -> dict[str, str]:
        return read_code_snapshots(raw_dir)
