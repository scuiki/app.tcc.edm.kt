# Testes herméticos da extração sandbox e do glob tolerante de layout, sem GPU e sem rede.

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from api.classroom_import.infrastructure.implementations import (
    progsnap_zip_extractor as discover_mod,
)
from api.classroom_import.infrastructure.implementations.progsnap_zip_extractor import (
    extract_zip,
    find_code_snapshots_file,
    find_main_tables,
)


def test_find_code_states_prefers_link_tables(ingest_layout_dir: Path) -> None:
    # na variante CodeWorkout de referência o CodeStates vive em LinkTables/, não em CodeStates/.
    found = find_code_snapshots_file(ingest_layout_dir)
    assert found is not None
    assert found == ingest_layout_dir / "LinkTables" / "CodeStates.csv"


def test_find_code_states_absent_returns_none(tmp_path: Path) -> None:
    assert find_code_snapshots_file(tmp_path) is None


def test_find_main_tables_enumerates_variants_sorted(ingest_layout_dir: Path) -> None:
    # All/ e Train/ → 2 candidatas; o extrator NÃO adivinha, lista para o professor escolher.
    mains = find_main_tables(ingest_layout_dir)
    assert len(mains) == 2
    assert mains == sorted(mains)
    assert {p.parent.name for p in mains} == {"All", "Train"}


def test_find_main_tables_empty_when_absent(tmp_path: Path) -> None:
    assert find_main_tables(tmp_path) == []


def test_the_layout_lists_every_main_table_and_the_code_snapshots(ingest_layout_dir: Path) -> None:
    assert len(find_main_tables(ingest_layout_dir)) == 2
    assert find_code_snapshots_file(ingest_layout_dir) == ingest_layout_dir / "LinkTables" / "CodeStates.csv"


def _make_zip(path: Path, members: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return path


def test_extract_zip_extracts_legitimate_member(tmp_path: Path) -> None:
    src = _make_zip(tmp_path / "ok.zip", {"All/MainTable.csv": "SubjectID\nS1\n"})
    dest = tmp_path / "raw"
    extract_zip(src, dest)
    assert (dest / "All" / "MainTable.csv").read_text() == "SubjectID\nS1\n"


def test_extract_zip_refuses_zip_slip(tmp_path: Path) -> None:
    # Membro com ../ tenta escapar do dest; deve levantar ANTES de escrever (zip-slip).
    src = _make_zip(tmp_path / "evil.zip", {"../evil.txt": "pwned"})
    dest = tmp_path / "raw"
    with pytest.raises(ValueError):
        extract_zip(src, dest)
    # O arquivo NÃO pode ter sido escrito fora do dest.
    assert not (tmp_path / "evil.txt").exists()


def test_extract_zip_refuses_absolute_path(tmp_path: Path) -> None:
    src = _make_zip(tmp_path / "abs.zip", {"/etc/evil.txt": "pwned"})
    dest = tmp_path / "raw"
    with pytest.raises(ValueError):
        extract_zip(src, dest)


def test_extract_zip_member_limit(tmp_path: Path) -> None:
    # Zip-bomb DoS, nº de membros acima do teto conservador levanta erro claro.
    members = {f"f{i}.txt": "x" for i in range(20_001)}
    src = _make_zip(tmp_path / "many.zip", members)
    dest = tmp_path / "raw"
    with pytest.raises(ValueError):
        extract_zip(src, dest)


def test_extract_zip_real_uncompressed_byte_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # O guarda conta bytes reais via streaming; baixamos o teto para provar que ele barra sozinho.
    monkeypatch.setattr(discover_mod, "_MAX_TOTAL_UNCOMPRESSED", 1024)  # 1 KiB
    monkeypatch.setattr(discover_mod, "_CHUNK", 256)  # força múltiplas leituras por membro
    src = _make_zip(tmp_path / "bomb.zip", {"big.txt": "A" * 4096})  # 4 KiB reais > 1 KiB
    dest = tmp_path / "raw"
    with pytest.raises(ValueError):
        extract_zip(src, dest)


def test_extract_zip_streaming_accepts_member_within_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Contraprova, conteúdo abaixo do teto passa pelo caminho de streaming e é escrito íntegro.
    monkeypatch.setattr(discover_mod, "_CHUNK", 16)  # múltiplos chunks num arquivo pequeno
    content = "SubjectID\n" + "S1\n" * 50
    src = _make_zip(tmp_path / "ok.zip", {"All/MainTable.csv": content})
    dest = tmp_path / "raw"
    extract_zip(src, dest)
    assert (dest / "All" / "MainTable.csv").read_text() == content



def test_upload_extraction_does_not_take_the_job_lock(tmp_db, tmp_path, monkeypatch):
    # O upload só escreve o cru; não pega a trava de job para não prendê-la até a escolha da tabela.
    import zipfile

    from api.shared.infrastructure import settings

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path / "data")
    upload = tmp_path / "upload.zip"
    with zipfile.ZipFile(upload, "w") as zf:
        zf.writestr("MainTable.csv", "SubjectID,AssignmentID\n")
        zf.writestr("CodeStates/CodeStates.csv", "CodeStateID,Code\n")

    detected = discover_mod.ProgSnapZipExtractor().extract(upload, "turma-x")

    assert detected.main_tables
    assert detected.raw_dir.exists()  # o cru fica preservado em raw/
    holder = tmp_db.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()[0]
    assert holder is None
