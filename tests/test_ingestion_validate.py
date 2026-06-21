"""Estágio B da ingestão — validate (pré-voo de falhas duras → ReportItem fatal, INGEST-01).

Testes herméticos: CSVs construídos em tmp_path (faltando coluna, bytes indecodáveis) e a
fixture `ingest_bom_csv`. Asseguram por severidade (não por strings de UI) que coluna
obrigatória ausente e encoding indecodável bloqueiam (fatal + DataFrame None — D-06), e que o
BOM NÃO bloqueia. Espelha o estilo testar-por-invariante do test_ingestion_report.
"""

from __future__ import annotations

from pathlib import Path

from edmkt_app.ingestion.validate import validate

_HEADER = "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp"
_ROW = "S1,439,1,c1,Run.Program,1.0,2019-03-01T08:00:00Z"


def _has_fatal(items) -> bool:
    return any(i.severity == "fatal" for i in items)


def test_coluna_obrigatoria_ausente_e_fatal(tmp_path: Path) -> None:
    # MainTable sem a coluna Score → falha dura específica desta ferramenta (Pitfall 1).
    main = tmp_path / "MainTable.csv"
    cols = "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,ServerTimestamp"
    main.write_text(f"{cols}\nS1,439,1,c1,Run.Program,2019-03-01T08:00:00Z\n", encoding="utf-8")

    df, items = validate(main)

    assert df is None  # D-06: qualquer fatal ⇒ nada a persistir
    fatals = [i for i in items if i.severity == "fatal"]
    assert any(i.check == "missing_required_column" for i in fatals)
    assert any("Score" in (i.location or "") for i in fatals)


def test_encoding_indecodavel_e_fatal(tmp_path: Path) -> None:
    # Bytes que não decodificam em utf-8(-sig) → ReportItem(check="encoding", fatal).
    main = tmp_path / "MainTable.csv"
    main.write_bytes(b"SubjectID\n\xff\xfe\x00\x80bad\n")

    df, items = validate(main)

    assert df is None
    assert any(i.check == "encoding" and i.severity == "fatal" for i in items)


def test_bom_nao_bloqueia(ingest_bom_csv: Path) -> None:
    # utf-8-sig consome o BOM transparente → SEM fatal (D-05 nível 2 = warning no clean).
    df, items = validate(ingest_bom_csv)

    assert not _has_fatal(items)
    assert df is not None
    assert "SubjectID" in df.columns  # BOM não vazou para o nome da 1ª coluna


def test_csv_valido_sem_fatal(tmp_path: Path) -> None:
    main = tmp_path / "MainTable.csv"
    main.write_text(f"{_HEADER}\n{_ROW}\n", encoding="utf-8")

    df, items = validate(main)

    assert not _has_fatal(items)
    assert df is not None
    # Coerção de tipos espelha data_loader: AssignmentID vira Int64 nullable.
    assert str(df["AssignmentID"].dtype) == "Int64"


def test_mensagem_fatal_nao_vaza_codigo_do_aluno(tmp_path: Path) -> None:
    # Information Disclosure (T-03-06): a mensagem carrega coluna/local, nunca bytes de código.
    secret = "SENHA_DO_ALUNO_NAO_DEVE_VAZAR"
    main = tmp_path / "MainTable.csv"
    cols = "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,ServerTimestamp,Code"
    main.write_text(
        f"{cols}\nS1,439,1,c1,Run.Program,2019-03-01T08:00:00Z,{secret}\n",
        encoding="utf-8",
    )

    _df, items = validate(main)

    for item in items:
        assert secret not in item.message
        assert secret not in (item.location or "")


def test_validate_nao_importa_nucleo_nem_persistence() -> None:
    import ast

    import edmkt_app.ingestion.validate as validate_mod

    tree = ast.parse(Path(validate_mod.__file__).read_text())
    modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any(
        m and (m.startswith("edmkt_core") or m.startswith("edmkt_app.persistence"))
        for m in modules
    )
