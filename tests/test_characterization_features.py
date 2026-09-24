"""Characterization tests for edmkt_core.features (D-04, CORE-06).

Lock the CURRENT behavior of the verbatim port through the public API on the
hermetic a439_mini fixture. These pin shapes/mappings before plans 02/03/04 touch
behavior. No real CSEDM, no AUC assertions.
"""

from __future__ import annotations

from edmkt_core.features import (
    build_code_input_tensor,
    build_vocab,
    extract_paths_javalang,
    paths_to_tensor,
)
from edmkt_core.sequences import build_sequences

_JAVA_OK = "public int f(int x) { return x + 1; }"
_JAVA_BAD = "public int oops( { return ;;; }"


def test_extract_paths_returns_paths_for_valid_java():
    paths = extract_paths_javalang(_JAVA_OK)
    assert len(paths) >= 1
    # Each path is a (start_token, path_string, end_token) triple.
    start, path_str, end = paths[0]
    assert isinstance(start, str) and isinstance(path_str, str) and isinstance(end, str)


def test_extract_paths_returns_empty_for_malformed_java():
    # T-01-01: the try/except DoS guard yields [] instead of crashing.
    assert extract_paths_javalang(_JAVA_BAD) == []


def test_build_vocab_returns_token_and_path_index_dicts():
    cache = {"c1": extract_paths_javalang(_JAVA_OK)}
    token_to_idx, path_to_idx = build_vocab(cache)
    assert isinstance(token_to_idx, dict) and isinstance(path_to_idx, dict)
    # 1-based indexing (0 reserved for OOV/PAD).
    assert all(idx >= 1 for idx in token_to_idx.values())
    assert all(idx >= 1 for idx in path_to_idx.values())


def test_paths_to_tensor_maps_unseen_token_to_zero():
    # CORE-04 seed: unseen start/path/end map to index 0 (OOV).
    paths = [("NeverSeenStart", "Never@Seen@Path", "NeverSeenEnd")]
    arr = paths_to_tensor(paths, token_to_idx={}, path_to_idx={}, R=50)
    assert arr.shape == (50, 3)
    assert arr[0, 0] == 0 and arr[0, 1] == 0 and arr[0, 2] == 0


def test_build_code_input_tensor_has_documented_last_dim(a439_mini):
    # Last dim == 2M + R*3, where M = number of distinct problems in the index.
    sequences = build_sequences(a439_mini, 439)
    cache = {
        csid: extract_paths_javalang(code)
        for csid, code in zip(
            a439_mini["code_snapshot_id"].astype(str), a439_mini["code"]
        )
    }
    token_to_idx, path_to_idx = build_vocab(cache)

    problem_ids = sorted(int(p) for p in a439_mini["problem_id"].unique())
    problem_to_idx = {pid: i for i, pid in enumerate(problem_ids)}
    M = len(problem_to_idx)
    R = 50

    X, Y_next, mask = build_code_input_tensor(
        sequences, cache, token_to_idx, path_to_idx, problem_to_idx, max_len=50, R=R
    )
    assert X.shape[-1] == 2 * M + R * 3
    assert Y_next.shape[-1] == M
    assert mask.shape[:2] == X.shape[:2]
