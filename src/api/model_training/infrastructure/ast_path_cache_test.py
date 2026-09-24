"""O cache em disco dos AST paths: reaproveita o já extraído, isola por turma, não vaza para o
vocabulário e não deixa um snapshot id escapar do diretório. Herméticos (data_root em tmp_path)."""

from __future__ import annotations

from pathlib import Path

import pytest

from api.model_training.infrastructure import ast_path_cache
from ml.code_dkt.student_split import build_train_only_vocabulary


def test_second_call_skips_extraction_same_result(
    data_root, cache_code_states, cache_config, monkeypatch
):
    snapshot_ids = ["c_ok1", "c_ok2"]
    calls = {"missing": []}
    real_build = ast_path_cache.extract_ast_paths_for_snapshots

    def counting_build(missing, code_by_snapshot, **kw):
        calls["missing"].append(list(missing))
        return real_build(missing, code_by_snapshot, **kw)

    monkeypatch.setattr(ast_path_cache, "extract_ast_paths_for_snapshots", counting_build)

    first = ast_path_cache.load_or_extract_ast_paths("A", snapshot_ids, cache_code_states, cache_config)
    second = ast_path_cache.load_or_extract_ast_paths("A", snapshot_ids, cache_code_states, cache_config)

    # First call extracts both; second sees them all cached → empty missing (or no call).
    assert sorted(calls["missing"][0]) == snapshot_ids
    assert all(len(m) == 0 for m in calls["missing"][1:])
    assert first == second


# --- namespace per turma ---------------------------------------------------


def test_namespace_isolation_no_cross_class_leak(java_snippets, data_root, cache_config):
    code_a = {"shared": java_snippets.ok_a}
    code_b = {"shared": java_snippets.empty_class}  # different code, same CSID

    res_a = ast_path_cache.load_or_extract_ast_paths("turma-a", ["shared"], code_a, cache_config)
    res_b = ast_path_cache.load_or_extract_ast_paths("turma-b", ["shared"], code_b, cache_config)

    file_a = data_root / "turma-a" / "cache" / "paths" / "shared.pkl"
    file_b = data_root / "turma-b" / "cache" / "paths" / "shared.pkl"
    assert file_a.exists() and file_b.exists()
    assert file_a != file_b
    # com_paths code yields paths; empty class yields none — proves no overwrite.
    assert len(res_a["shared"]) > 0
    assert res_b["shared"] == []


# --- 3-way classification --------------------------------------------------


def test_global_cache_does_not_leak_into_train_vocab(java_snippets, data_root, cache_config):
    # Cache ALL snapshot_ids globally (com_paths each), then build vocab train-only.
    code_states = {"train1": java_snippets.ok_a, "held_out": "public int z(int q) { return q * 2; }"}
    ast_paths_by_snapshot = ast_path_cache.load_or_extract_ast_paths(
        "A", ["train1", "held_out"], code_states, cache_config
    )
    token_to_idx, path_to_idx = build_train_only_vocabulary(ast_paths_by_snapshot, ["train1"])

    held_paths = ast_paths_by_snapshot["held_out"]
    assert held_paths, "held-out must have paths for the OOV check to be meaningful"
    oov = sum(
        1
        for start, path_str, end in held_paths
        if path_str not in path_to_idx
    )
    assert oov > 0  # held-out paths absent from train-only vocab → OOV>0 (no leak)


# --- traversal guard --------------------------------------------------


def test_malicious_csid_cannot_escape_cache_dir(java_snippets, data_root, cache_config):
    code_states = {"../../etc/x": java_snippets.ok_a}
    with pytest.raises((ValueError, OSError)):
        ast_path_cache.load_or_extract_ast_paths("A", ["../../etc/x"], code_states, cache_config)

    escaped = (data_root / ".." / ".." / "etc" / "x.pkl").resolve()
    assert not Path(escaped).exists()
