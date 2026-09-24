# Caracterização da extração de AST paths e do vocabulário (numérica congelada do TCC 1).

from __future__ import annotations

from ml.code_dkt.ast_paths import build_ast_path_vocabulary, extract_ast_paths

_JAVA_OK = "public int f(int x) { return x + 1; }"
_JAVA_BAD = "public int oops( { return ;;; }"


def test_extract_paths_returns_paths_for_valid_java():
    paths = extract_ast_paths(_JAVA_OK)
    assert len(paths) >= 1
    # Cada path é uma tripla (start_token, path_string, end_token).
    start, path_str, end = paths[0]
    assert isinstance(start, str) and isinstance(path_str, str) and isinstance(end, str)


def test_extract_paths_returns_empty_for_malformed_java():
    # A guarda try/except contra DoS devolve [] em vez de estourar exceção.
    assert extract_ast_paths(_JAVA_BAD) == []


def test_build_vocab_returns_token_and_path_index_dicts():
    cache = {"c1": extract_ast_paths(_JAVA_OK)}
    token_to_idx, path_to_idx = build_ast_path_vocabulary(cache)
    assert isinstance(token_to_idx, dict) and isinstance(path_to_idx, dict)
    # Indexação começa em 1 (0 é reservado para OOV/PAD).
    assert all(idx >= 1 for idx in token_to_idx.values())
    assert all(idx >= 1 for idx in path_to_idx.values())
