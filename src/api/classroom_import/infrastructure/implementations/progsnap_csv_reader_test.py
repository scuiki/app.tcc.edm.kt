"""Leitura do MainTable (pré-voo de falhas duras → ImportCheck fatal).

Testes herméticos: CSVs construídos em tmp_path (faltando coluna, bytes indecodáveis) e a
fixture `ingest_bom_csv`. Asseguram por severidade (não por strings de UI) que coluna
obrigatória ausente e encoding indecodável bloqueiam (fatal + DataFrame None), e que o
BOM NÃO bloqueia. 
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from api.classroom_import.infrastructure.implementations.progsnap_csv_reader import read_main_table

_HEADER = "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp"
_ROW = "S1,439,1,c1,Run.Program,1.0,2019-03-01T08:00:00Z"


def _has_fatal(items) -> bool:
    return any(i.severity == "fatal" for i in items)


def test_coluna_obrigatoria_ausente_e_fatal(tmp_path: Path) -> None:
    # MainTable sem a coluna Score → falha dura específica desta ferramenta.
    main = tmp_path / "MainTable.csv"
    cols = "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,ServerTimestamp"
    main.write_text(f"{cols}\nS1,439,1,c1,Run.Program,2019-03-01T08:00:00Z\n", encoding="utf-8")

    df, items = read_main_table(main)

    assert df is None  # qualquer fatal ⇒ nada a persistir
    fatals = [i for i in items if i.severity == "fatal"]
    assert any(i.check == "missing_required_column" for i in fatals)
    assert any("Score" in (i.location or "") for i in fatals)


def test_encoding_indecodavel_e_fatal(tmp_path: Path) -> None:
    # Bytes que não decodificam em utf-8(-sig) → ImportCheck(check="encoding", fatal).
    main = tmp_path / "MainTable.csv"
    main.write_bytes(b"SubjectID\n\xff\xfe\x00\x80bad\n")

    df, items = read_main_table(main)

    assert df is None
    assert any(i.check == "encoding" and i.severity == "fatal" for i in items)


def test_bom_nao_bloqueia(ingest_bom_csv: Path) -> None:
    # utf-8-sig consome o BOM transparente → SEM fatal.
    df, items = read_main_table(ingest_bom_csv)

    assert not _has_fatal(items)
    assert df is not None
    assert "SubjectID" in df.columns  # BOM não vazou para o nome da 1ª coluna


def test_csv_valido_sem_fatal(tmp_path: Path) -> None:
    main = tmp_path / "MainTable.csv"
    main.write_text(f"{_HEADER}\n{_ROW}\n", encoding="utf-8")

    df, items = read_main_table(main)

    assert not _has_fatal(items)
    assert df is not None
    # Coerção de tipos espelha data_loader: AssignmentID vira Int64 nullable.
    assert str(df["AssignmentID"].dtype) == "Int64"


def test_mensagem_fatal_nao_vaza_codigo_do_aluno(tmp_path: Path) -> None:
    # Information Disclosure: a mensagem carrega coluna/local, nunca bytes de código.
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


def test_score_string_e_coagido_a_numerico(tmp_path: Path) -> None:
    # CR-01: ProgSnap2 real traz Score como string. Um token que o pandas NÃO reconhece como NaN
    # nativo (ex.: "erro") força a coluna inteira a object — aí `Score == 1.0` falha p/ toda linha
    # (binarização D-12 zera em silêncio) e `float(row.Score)` estoura no persist.
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
    # Coluna numérica (não object): pré-condição para `Score == 1.0` e `float(row.Score)`.
    assert pd.api.types.is_numeric_dtype(df["Score"])
    # Binarização correta sobre o tipo coagido: só o "1.0" vira correct=1.
    correct = ((df["EventType"] == "Run.Program") & (df["Score"] == 1.0)).astype(int)
    assert correct.tolist() == [1, 0, 0, 0]
    # "erro" e vazio viram NaN → pd.isna verdadeiro (persist null-ifica em vez de estourar float).
    assert df["Score"].isna().tolist() == [False, False, True, True]


def test_score_nao_numerico_emite_warning_graduado(tmp_path: Path) -> None:
    # O warning conta SÓ coerções que falharam de verdade: valores que tinham conteúdo mas não
    # eram numéricos ("erro"). Vazio/"N/A" já chegam NaN do read_csv, então não são "falha de
    # coerção" — são ausência, contada pelo persist/viability, não aqui.
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


def test_score_todo_numerico_sem_warning(tmp_path: Path) -> None:
    main = tmp_path / "MainTable.csv"
    main.write_text(f"{_HEADER}\n{_ROW}\n", encoding="utf-8")

    _df, items = read_main_table(main)

    assert not any(i.check == "score_coercion" for i in items)


