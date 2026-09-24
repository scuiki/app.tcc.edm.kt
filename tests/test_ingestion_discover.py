"""Estágio A da ingestão — discover (glob tolerante de layout + extração sandbox).

Testes herméticos (sem GPU, sem rede): usam a fixture `ingest_layout_dir` (CodeStates em
LinkTables/ + múltiplas MainTable) e zips construídos em tmp_path. Asseguram invariantes de
localização (D-02/D-03) e a defesa contra zip-slip/zip-bomb por comportamento (ValueError +
ausência de arquivo escrito fora do dest), nunca por valores mágicos.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from edmkt_app.ingestion import discover as discover_mod
from edmkt_app.ingestion.discover import (
    detect_variants,
    extract_zip,
    find_code_states,
    find_main_tables,
)


def test_find_code_states_prefere_link_tables(ingest_layout_dir: Path) -> None:
    # D-02: na variante CodeWorkout de referência o CodeStates vive em LinkTables/, não em CodeStates/.
    found = find_code_states(ingest_layout_dir)
    assert found is not None
    assert found == ingest_layout_dir / "LinkTables" / "CodeStates.csv"


def test_find_code_states_ausente_devolve_none(tmp_path: Path) -> None:
    assert find_code_states(tmp_path) is None


def test_find_main_tables_enumera_variantes_ordenadas(ingest_layout_dir: Path) -> None:
    # D-03: All/ e Train/ → 2 candidatas; discover NÃO adivinha, lista para o professor escolher.
    mains = find_main_tables(ingest_layout_dir)
    assert len(mains) == 2
    assert mains == sorted(mains)
    assert {p.parent.name for p in mains} == {"All", "Train"}


def test_find_main_tables_vazio_quando_ausente(tmp_path: Path) -> None:
    assert find_main_tables(tmp_path) == []


def test_detect_variants_estrutura_read_only(ingest_layout_dir: Path) -> None:
    info = detect_variants(ingest_layout_dir)
    assert len(info["main_tables"]) == 2
    assert info["code_states"] == ingest_layout_dir / "LinkTables" / "CodeStates.csv"


def _make_zip(path: Path, members: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return path


def test_extract_zip_extrai_membro_legitimo(tmp_path: Path) -> None:
    src = _make_zip(tmp_path / "ok.zip", {"All/MainTable.csv": "SubjectID\nS1\n"})
    dest = tmp_path / "raw"
    extract_zip(src, dest)
    assert (dest / "All" / "MainTable.csv").read_text() == "SubjectID\nS1\n"


def test_extract_zip_rejeita_zip_slip(tmp_path: Path) -> None:
    # Membro com ../ tenta escapar do dest; deve levantar ANTES de escrever (zip-slip).
    src = _make_zip(tmp_path / "evil.zip", {"../evil.txt": "pwned"})
    dest = tmp_path / "raw"
    with pytest.raises(ValueError):
        extract_zip(src, dest)
    # O arquivo NÃO pode ter sido escrito fora do dest.
    assert not (tmp_path / "evil.txt").exists()


def test_extract_zip_rejeita_path_absoluto(tmp_path: Path) -> None:
    src = _make_zip(tmp_path / "abs.zip", {"/etc/evil.txt": "pwned"})
    dest = tmp_path / "raw"
    with pytest.raises(ValueError):
        extract_zip(src, dest)


def test_extract_zip_teto_de_membros(tmp_path: Path) -> None:
    # Zip-bomb DoS: nº de membros acima do teto conservador levanta erro claro.
    members = {f"f{i}.txt": "x" for i in range(20_001)}
    src = _make_zip(tmp_path / "many.zip", members)
    dest = tmp_path / "raw"
    with pytest.raises(ValueError):
        extract_zip(src, dest)


def test_extract_zip_teto_de_bytes_reais_descomprimidos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # CR-02: o guarda autoritativo conta bytes DESCOMPRIMIDOS reais via streaming, não o header
    # atacante-controlado. Em vez de gerar GiB, abaixamos o teto para um valor pequeno e provamos
    # que conteúdo real acima dele aborta — o pre-check por file_size sozinho não pegaria isto.
    monkeypatch.setattr(discover_mod, "_MAX_TOTAL_UNCOMPRESSED", 1024)  # 1 KiB
    monkeypatch.setattr(discover_mod, "_CHUNK", 256)  # força múltiplas leituras por membro
    src = _make_zip(tmp_path / "bomb.zip", {"big.txt": "A" * 4096})  # 4 KiB reais > 1 KiB
    dest = tmp_path / "raw"
    with pytest.raises(ValueError):
        extract_zip(src, dest)


def test_extract_zip_streaming_aceita_membro_dentro_do_teto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Contraprova: conteúdo abaixo do teto passa pelo caminho de streaming e é escrito íntegro.
    monkeypatch.setattr(discover_mod, "_CHUNK", 16)  # múltiplos chunks num arquivo pequeno
    content = "SubjectID\n" + "S1\n" * 50
    src = _make_zip(tmp_path / "ok.zip", {"All/MainTable.csv": content})
    dest = tmp_path / "raw"
    extract_zip(src, dest)
    assert (dest / "All" / "MainTable.csv").read_text() == content


def test_discover_nao_importa_nucleo_nem_trava() -> None:
    # Lock Timing (Pitfall 5): a detecção é read-only e NÃO toca PipelineLock nem o núcleo.
    # Checa o CÓDIGO (não a docstring/prosa): nenhuma menção a PipelineLock ou import do
    # núcleo fora de literais de string/comentários.
    import ast

    import edmkt_app.ingestion.discover as discover

    tree = ast.parse(Path(discover.__file__).read_text())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "PipelineLock" not in names and "PipelineLock" not in imported
    assert not any(m and (m == "ml" or m.startswith("ml.")) for m in modules)
