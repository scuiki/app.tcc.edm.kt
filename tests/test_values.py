"""CodeStateId: o id do ProgSnap2 que vira nome de arquivo no cache de AST paths."""

from __future__ import annotations

import pytest

from edmkt_app import values


def test_code_state_id_accepts_the_shapes_the_dataset_uses():
    for ok in ("c1", "abc-123", "state_42", "v1.2"):
        assert str(values.CodeStateId(ok)) == ok


@pytest.mark.parametrize("bad", ["", "..", "a/b", "../etc", "a b", "c\x00d", "ç"])
def test_code_state_id_rejects_anything_that_could_escape_a_directory(bad):
    with pytest.raises(ValueError):
        values.CodeStateId(bad)


# --- ConfinedPath: resolve-depois-confere sob uma raiz --------------------------------------
