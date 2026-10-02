# Caracterização da extração de AST paths, da amostragem aleatória dos R paths e do vocabulário.

from __future__ import annotations

import hashlib
import random
import sys

from ml.code_dkt.ast_paths import (
    PADDING_INDEX,
    UNKNOWN_INDEX,
    build_ast_path_vocabulary,
    extract_ast_paths,
    sample_ast_paths,
)
from tests.fixtures.sample_data import JAVA_LONG, JAVA_OK_A, JAVA_OK_B, JAVA_OK_C

_JAVA_OK = "public int f(int x) { return x + 1; }"
_JAVA_BAD = "public int oops( { return ;;; }"

# A amostragem aleatória de 100 paths do JAVA_LONG que o extract_ast_paths fazia por dentro, seed 42
_R100_DRAW_SHA256 = "b367533d88ab5323bd193618df5938fcf1293f3cf0e646a0c3ae6031cc083f50"


def test_process_runs_with_hash_seed_zero():
    # A ordem dos modificadores Java sai de um set e depende do PYTHONHASHSEED, que o app fixa em 0
    assert sys.flags.hash_randomization == 0, (
        "PYTHONHASHSEED não é 0 neste processo, e os AST paths não saem na ordem que o app fixa"
    )


def test_extract_paths_returns_paths_for_valid_java():
    paths = extract_ast_paths(_JAVA_OK)
    assert len(paths) >= 1
    # Cada path é uma tripla (start_token, path_string, end_token).
    start, path_str, end = paths[0]
    assert isinstance(start, str) and isinstance(path_str, str) and isinstance(end, str)


def test_extract_paths_returns_empty_for_malformed_java():
    # A guarda try/except contra DoS devolve [] em vez de estourar exceção.
    assert extract_ast_paths(_JAVA_BAD) == []


def test_extract_returns_every_path_of_the_solution():
    # O extrator não amostra, o vocabulário conta todos e a amostragem fica na montagem da entrada
    assert len(extract_ast_paths(JAVA_LONG)) == 142


def test_sample_keeps_a_solution_with_up_to_r_paths():
    paths = extract_ast_paths(_JAVA_OK)
    assert sample_ast_paths(paths, R=100, path_sampling_seed=42) == paths


def test_sample_is_the_r100_draw_of_the_previous_extractor():
    sample = sample_ast_paths(extract_ast_paths(JAVA_LONG), R=100, path_sampling_seed=42)
    assert len(sample) == 100
    assert hashlib.sha256(repr(sample).encode()).hexdigest() == _R100_DRAW_SHA256


def test_sample_does_not_depend_on_call_order_or_global_random_state():
    solutions = [extract_ast_paths(c) for c in (JAVA_LONG, JAVA_OK_A, JAVA_OK_B, JAVA_OK_C)]
    alone = [sample_ast_paths(p, R=10, path_sampling_seed=42) for p in solutions]

    # Outra ordem e o gerador global mexido, e cada solução continua com a mesma amostra
    random.seed(7)
    random.random()
    reversed_order = [sample_ast_paths(p, R=10, path_sampling_seed=42) for p in solutions[::-1]]
    assert reversed_order[::-1] == alone


def test_vocabulary_reserves_padding_and_unknown():
    assert (PADDING_INDEX, UNKNOWN_INDEX) == (0, 1)
    cache = {"c1": extract_ast_paths(_JAVA_OK), "c2": extract_ast_paths(JAVA_LONG)}
    token_to_idx, path_to_idx = build_ast_path_vocabulary(cache)

    # Os tokens reais começam no 2, contíguos, e as sentinelas não entram no dicionário
    assert sorted(token_to_idx.values()) == list(range(2, 2 + len(token_to_idx)))
    assert sorted(path_to_idx.values()) == list(range(2, 2 + len(path_to_idx)))
    all_paths = {p for paths in cache.values() for _, p, _ in paths}
    assert set(path_to_idx) == all_paths
