"""Caracterização da tensorização da entrada do Code-DKT (numérica congelada do TCC 1)."""

from __future__ import annotations

from ml.code_dkt.ast_paths import build_ast_path_vocabulary, extract_ast_paths
from ml.code_dkt.model_input import ast_paths_to_index_array, build_model_input_tensors
from ml.code_dkt.student_sequences import build_student_sequences


def test_paths_to_tensor_maps_unseen_token_to_zero():
    # unseen start/path/end map to index 0 (OOV).
    paths = [("NeverSeenStart", "Never@Seen@Path", "NeverSeenEnd")]
    arr = ast_paths_to_index_array(paths, token_to_idx={}, path_to_idx={}, R=50)
    assert arr.shape == (50, 3)
    assert arr[0, 0] == 0 and arr[0, 1] == 0 and arr[0, 2] == 0


def test_build_code_input_tensor_has_documented_last_dim(a439_mini):
    # Last dim == 2M + R*3, where M = number of distinct problems in the index.
    sequences = build_student_sequences(a439_mini, 439)
    cache = {
        snapshot_id: extract_ast_paths(code)
        for snapshot_id, code in zip(
            a439_mini["code_snapshot_id"].astype(str), a439_mini["code"]
        )
    }
    token_to_idx, path_to_idx = build_ast_path_vocabulary(cache)

    problem_ids = sorted(int(p) for p in a439_mini["problem_id"].unique())
    problem_to_idx = {pid: i for i, pid in enumerate(problem_ids)}
    M = len(problem_to_idx)
    R = 50

    X, Y_next, mask = build_model_input_tensors(
        sequences, cache, token_to_idx, path_to_idx, problem_to_idx, max_len=50, R=R
    )
    assert X.shape[-1] == 2 * M + R * 3
    assert Y_next.shape[-1] == M
    assert mask.shape[:2] == X.shape[:2]
