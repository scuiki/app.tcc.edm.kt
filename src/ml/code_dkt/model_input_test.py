# Caracterização da tensorização da entrada do Code-DKT, com a amostragem dos R paths por solução.

from __future__ import annotations

import pandas as pd
import torch

from ml.code_dkt.ast_paths import (
    PADDING_INDEX,
    UNKNOWN_INDEX,
    build_ast_path_vocabulary,
    extract_ast_paths,
    sample_ast_paths,
)
from ml.code_dkt.model_input import ast_paths_to_index_array, build_model_input_tensors
from ml.code_dkt.student_sequences import build_student_sequences
from tests.fixtures.sample_data import JAVA_LONG, JAVA_OK_A, cleaned_row, with_cleaned_dtypes


def test_unseen_paths_map_to_unknown_and_empty_slots_to_padding():
    paths = [("NeverSeenStart", "Never@Seen@Path", "NeverSeenEnd")]
    arr = ast_paths_to_index_array(paths, token_to_idx={}, path_to_idx={}, R=50)
    assert arr.shape == (50, 3)
    assert arr[0].tolist() == [UNKNOWN_INDEX] * 3
    assert (arr[1:] == PADDING_INDEX).all()


def test_index_array_takes_the_sample_and_not_the_first_r_paths():
    paths = extract_ast_paths(JAVA_LONG)
    token_to_idx, path_to_idx = build_ast_path_vocabulary({"long": paths})
    sample = sample_ast_paths(paths, R=100, path_sampling_seed=42)
    assert sample != paths[:100]

    arr = ast_paths_to_index_array(paths, token_to_idx, path_to_idx, R=100, path_sampling_seed=42)
    assert arr[:, 1].tolist() == [path_to_idx[p] for _, p, _ in sample]


def test_build_code_input_tensor_has_documented_last_dim(a439_mini):
    # Última dimensão é 2M + R*3, com M igual ao número de problemas distintos no índice.
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
    R = 100

    X, Y_next, mask = build_model_input_tensors(
        sequences, cache, token_to_idx, path_to_idx, problem_to_idx, max_len=50, R=R
    )
    assert X.shape[-1] == 2 * M + R * 3
    assert Y_next.shape[-1] == M
    assert mask.shape[:2] == X.shape[:2]


def test_a_student_gets_the_same_input_alone_or_with_others():
    # A inferência e a avaliação vão em lotes de 64 alunos, e a entrada de cada um não muda
    rows = [
        cleaned_row("S1", 1, "2019-03-01T08:00:00Z", "Run.Program", 0.0, JAVA_OK_A, "a"),
        cleaned_row("S2", 1, "2019-03-01T09:00:00Z", "Run.Program", 0.0, JAVA_LONG, "b"),
        cleaned_row("S2", 2, "2019-03-01T09:01:00Z", "Run.Program", 1.0, JAVA_LONG, "c"),
    ]
    sequences = build_student_sequences(with_cleaned_dtypes(pd.DataFrame(rows)), 439)
    cache = {sid: extract_ast_paths(code) for sid, code in [("a", JAVA_OK_A), ("b", JAVA_LONG), ("c", JAVA_LONG)]}
    token_to_idx, path_to_idx = build_ast_path_vocabulary(cache)
    problem_to_idx = {1: 0, 2: 1}

    together, _, _ = build_model_input_tensors(sequences, cache, token_to_idx, path_to_idx, problem_to_idx)
    alone, _, _ = build_model_input_tensors(sequences[1:], cache, token_to_idx, path_to_idx, problem_to_idx)
    assert torch.equal(together[1], alone[0])
