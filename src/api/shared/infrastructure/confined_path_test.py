"""ConfinedPath: construí-lo é a prova de que o caminho está sob a raiz (resolve e depois confere)."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.shared.infrastructure.confined_path import ConfinedPath


def test_confined_path_accepts_a_path_under_the_root(tmp_path):
    target = tmp_path / "clean" / "a.parquet"
    assert Path(ConfinedPath(target, root=tmp_path)) == target.resolve()


def test_confined_path_accepts_the_root_itself(tmp_path):
    assert Path(ConfinedPath(tmp_path, root=tmp_path)) == tmp_path.resolve()


def test_confined_path_rejects_traversal_out_of_the_root(tmp_path):
    # O caso real (CR-01): main_table="/etc/passwd" viraria leitura arbitrária via pandas.
    with pytest.raises(ValueError):
        ConfinedPath(Path("/etc/passwd"), root=tmp_path)
    with pytest.raises(ValueError):
        ConfinedPath(tmp_path / ".." / "fora", root=tmp_path)


def test_confined_path_resolves_before_checking(tmp_path):
    # Confere no caminho JÁ resolvido: um ".." no meio que volta para dentro é legítimo e deve
    # passar — a guarda é sobre o destino real, não sobre a aparência da string.
    (tmp_path / "a").mkdir()
    inside = tmp_path / "a" / ".." / "b.parquet"
    assert Path(ConfinedPath(inside, root=tmp_path)) == (tmp_path / "b.parquet").resolve()


# --- ProgSnapAssignmentId: o id do ProgSnap2, distinto do id do banco (999.2) ---------------
