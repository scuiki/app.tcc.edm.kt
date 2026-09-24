"""Fixtures do code_dkt: as entradas mínimas de treino a partir do a439_mini."""

from __future__ import annotations

import pytest

from ml.code_dkt.ast_paths import build_ast_path_vocabulary, extract_ast_paths
from ml.code_dkt.problem_index import build_problem_index
from ml.code_dkt.student_sequences import build_student_sequences


@pytest.fixture
def training_inputs(a439_mini):
    """(sequences, ast_paths_by_snapshot, vocab, problem_to_idx, config) para um treino curto em CPU."""
    sequences = build_student_sequences(a439_mini, 439)
    cache = {
        snapshot_id: extract_ast_paths(code)
        for snapshot_id, code in zip(
            a439_mini["code_snapshot_id"].astype(str), a439_mini["code"]
        )
    }
    token_to_idx, path_to_idx = build_ast_path_vocabulary(cache)
    vocab = {
        "token_to_idx": token_to_idx,
        "path_to_idx": path_to_idx,
        "node_count": len(token_to_idx),
        "path_count": len(path_to_idx),
    }
    problem_to_idx = build_problem_index(sequences)
    # Architecture frozen; only epoch count reduced for a fast smoke run.
    config = {"hidden_dim": 128, "dropout": 0.1, "lr": 5e-4,
              "batch_size": 128, "epochs": 3, "max_len": 50, "R": 50}
    return sequences, cache, vocab, problem_to_idx, config
