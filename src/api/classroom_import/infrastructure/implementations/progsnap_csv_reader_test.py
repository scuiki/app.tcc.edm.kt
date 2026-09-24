# Testes herméticos do pré-voo de falhas duras do MainTable, por severidade, não por UI.

from __future__ import annotations

from pathlib import Path

import pandas as pd

from api.classroom_import.infrastructure.implementations.progsnap_csv_reader import read_main_table

_HEADER = "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp"
_ROW = "S1,439,1,c1,Run.Program,1.0,2019-03-01T08:00:00Z"


def _has_fatal(items) -> bool:
    return any(i.severity == "fatal" for i in items)


def test_missing_required_column_is_fatal(tmp_path: Path) -> None:
    # MainTable sem a coluna Score → falha dura específica desta ferramenta.
    main = tmp_path / "MainTable.csv"
    cols = "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,ServerTimestamp"
    main.write_text(f"{cols}\nS1,439,1,c1,Run.Program,2019-03-01T08:00:00Z\n", encoding="utf-8")

    df, items = read_main_table(main)

    assert df is None  # qualquer fatal ⇒ nada a persistir
    fatals = [i for i in items if i.severity == "fatal"]
    assert any(i.check == "missing_required_column" for i in fatals)
    assert any("Score" in (i.location or "") for i in fatals)


def test_undecodable_encoding_is_fatal(tmp_path: Path) -> None:
    # Bytes que não decodificam em utf-8(-sig) → ImportCheck(check="encoding", fatal).
    main = tmp_path / "MainTable.csv"
    main.write_bytes(b"SubjectID\n\xff\xfe\x00\x80bad\n")

    df, items = read_main_table(main)

    assert df is None
    assert any(i.check == "encoding" and i.severity == "fatal" for i in items)


def test_bom_does_not_block(ingest_bom_csv: Path) -> None:
    # utf-8-sig consome o BOM transparente → SEM fatal.
    df, items = read_main_table(ingest_bom_csv)

    assert not _has_fatal(items)
    assert df is not None
    assert "SubjectID" in df.columns  # BOM não vazou para o nome da 1ª coluna


def test_valid_csv_has_no_fatal(tmp_path: Path) -> None:
    main = tmp_path / "MainTable.csv"
    main.write_text(f"{_HEADER}\n{_ROW}\n", encoding="utf-8")

    df, items = read_main_table(main)

    assert not _has_fatal(items)
    assert df is not None
    # A mesma coerção de tipos do TCC 1; AssignmentID vira Int64 nullable.
    assert str(df["AssignmentID"].dtype) == "Int64"


def test_fatal_message_does_not_leak_student_code(tmp_path: Path) -> None:
    # Information Disclosure, a mensagem carrega coluna/local, nunca bytes de código.
    secret = "SENHA_DO_ALUNO_NAO_DEVE_VAZAR"
    main = tmp_path / "MainTable.csv"
    cols = "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,ServerTimestamp,Code"
    main.write_text(
        f"{cols}\nS1,439,1,c1,Run.Program,2019-03-01T08:00:00Z,{secret}\n",
        encoding="utf-8",
    )

    _df, items = read_main_table(main)

    for item in items:
        assert secret not in item.message
        assert secret not in (item.location or "")


def test_score_string_is_coerced_to_numeric(tmp_path: Path) -> None:
    # ProgSnap2 real traz Score como string; token não-NaN nativo força object e quebra Score==1.0.
    main = tmp_path / "MainTable.csv"
    rows = [
        "S1,439,1,c1,Run.Program,1.0,2019-03-01T08:00:00Z",  # acerto
        "S2,439,1,c2,Run.Program,0,2019-03-01T08:01:00Z",  # erro
        "S3,439,1,c3,Run.Program,erro,2019-03-01T08:02:00Z",  # lixo não-NaN-nativo → object
        'S4,439,1,c4,Run.Program,,2019-03-01T08:03:00Z',  # vazio → já NaN no read_csv
    ]
    main.write_text(f"{_HEADER}\n" + "\n".join(rows) + "\n", encoding="utf-8")

    df, items = read_main_table(main)

    assert df is not None
    assert not _has_fatal(items)
    # Coluna numérica (não object), pré-condição para `Score == 1.0` e `float(row.Score)`.
    assert pd.api.types.is_numeric_dtype(df["Score"])
    # Binarização correta sobre o tipo coagido; só o "1.0" vira correct=1.
    correct = ((df["EventType"] == "Run.Program") & (df["Score"] == 1.0)).astype(int)
    assert correct.tolist() == [1, 0, 0, 0]
    # "erro" e vazio viram NaN → pd.isna verdadeiro (persist null-ifica em vez de estourar float).
    assert df["Score"].isna().tolist() == [False, False, True, True]


def test_non_numeric_score_emits_graduated_warning(tmp_path: Path) -> None:
    # O warning conta só coerção que falhou de verdade; vazio/N/A já chegam NaN e não contam.
    main = tmp_path / "MainTable.csv"
    rows = [
        "S1,439,1,c1,Run.Program,1.0,2019-03-01T08:00:00Z",
        "S2,439,1,c2,Run.Program,erro,2019-03-01T08:01:00Z",  # falha de coerção real
        "S3,439,1,c3,Run.Program,N/A,2019-03-01T08:02:00Z",  # já NaN no read_csv (não conta)
        'S4,439,1,c4,Run.Program,,2019-03-01T08:03:00Z',  # já NaN no read_csv (não conta)
    ]
    main.write_text(f"{_HEADER}\n" + "\n".join(rows) + "\n", encoding="utf-8")

    _df, items = read_main_table(main)

    warns = [i for i in items if i.check == "score_coercion"]
    assert len(warns) == 1
    assert warns[0].severity == "warning"
    assert warns[0].count == 1  # só o "erro"


def test_all_numeric_score_has_no_warning(tmp_path: Path) -> None:
    main = tmp_path / "MainTable.csv"
    main.write_text(f"{_HEADER}\n{_ROW}\n", encoding="utf-8")

    _df, items = read_main_table(main)

    assert not any(i.check == "score_coercion" for i in items)


