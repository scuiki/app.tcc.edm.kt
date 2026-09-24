"""MODEL-05 coverage for the on-disk incremental feature cache + 3-way parse classifier.

All hermetic: Java snippets are code-built (conftest `_JAVA_*` + cache_code_states), never
the real CSEDM. DATA_ROOT is monkeypatched to tmp_path (mirrors test_ingestion_service), so
no test writes under the repo's data/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from edmkt_app import features_cache, settings
from ml.code_dkt.student_split import build_train_only_vocabulary



@pytest.fixture
def data_root(tmp_path, monkeypatch):
    """Point features_cache.DATA_ROOT at tmp_path so .pkl writes stay hermetic."""
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    return tmp_path


# --- incremental skip (D-07/D-08) -------------------------------------------------


def test_second_call_skips_extraction_same_result(
    data_root, cache_code_states, cache_config, monkeypatch
):
    snapshot_ids = ["c_ok1", "c_ok2"]
    calls = {"missing": []}
    real_build = features_cache.extract_ast_paths_for_snapshots

    def counting_build(missing, code_states, **kw):
        calls["missing"].append(list(missing))
        return real_build(missing, code_states, **kw)

    monkeypatch.setattr(features_cache, "extract_ast_paths_for_snapshots", counting_build)

    first = features_cache.build_cache_on_disk("A", snapshot_ids, cache_code_states, cache_config)
    second = features_cache.build_cache_on_disk("A", snapshot_ids, cache_code_states, cache_config)

    # First call extracts both; second sees them all cached → empty missing (or no call).
    assert sorted(calls["missing"][0]) == snapshot_ids
    assert all(len(m) == 0 for m in calls["missing"][1:])
    assert first == second


# --- namespace per turma (D-07) ---------------------------------------------------


def test_namespace_isolation_no_cross_class_leak(java_snippets, data_root, cache_config):
    code_a = {"shared": java_snippets.ok_a}
    code_b = {"shared": java_snippets.empty_class}  # different code, same CSID

    res_a = features_cache.build_cache_on_disk("turma-a", ["shared"], code_a, cache_config)
    res_b = features_cache.build_cache_on_disk("turma-b", ["shared"], code_b, cache_config)

    file_a = data_root / "turma-a" / "cache" / "paths" / "shared.pkl"
    file_b = data_root / "turma-b" / "cache" / "paths" / "shared.pkl"
    assert file_a.exists() and file_b.exists()
    assert file_a != file_b
    # com_paths code yields paths; empty class yields none — proves no overwrite.
    assert len(res_a["shared"]) > 0
    assert res_b["shared"] == []


# --- 3-way classification (D-09) --------------------------------------------------


def test_classify_parse_three_way(java_snippets, cache_config):
    assert features_cache.classify_parse(java_snippets.bad, cache_config) == "parse_failed"
    assert features_cache.classify_parse(java_snippets.ok_a, cache_config) == "com_paths"
    assert features_cache.classify_parse("   ", cache_config) == "no_code"
    assert features_cache.classify_parse(java_snippets.empty_class, cache_config) == "parsed_sem_paths"


def test_parse_rate_excludes_no_code_from_denominator(cache_code_states, cache_config):
    # c_ok1/c_ok2=com_paths, c_empty=parsed_sem_paths, c_bad=parse_failed, c_blank=no_code.
    rate = features_cache.parse_rate(list(cache_code_states.values()), cache_config)
    # denominator = 4 (excludes c_blank); numerator = com_paths + parsed_sem_paths = 3.
    assert rate == pytest.approx(3 / 4)


# --- no-leak invariant: train-only vocab still OOV on held-out (CORE-04, D-08) ----


def test_global_cache_does_not_leak_into_train_vocab(java_snippets, data_root, cache_config):
    # Cache ALL snapshot_ids globally (com_paths each), then build vocab train-only.
    code_states = {"train1": java_snippets.ok_a, "held_out": "public int z(int q) { return q * 2; }"}
    ast_paths_by_snapshot = features_cache.build_cache_on_disk(
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


# --- traversal guard (T-04-CSID) --------------------------------------------------


def test_malicious_csid_cannot_escape_cache_dir(java_snippets, data_root, cache_config):
    code_states = {"../../etc/x": java_snippets.ok_a}
    with pytest.raises((ValueError, OSError)):
        features_cache.build_cache_on_disk("A", ["../../etc/x"], code_states, cache_config)

    escaped = (data_root / ".." / ".." / "etc" / "x.pkl").resolve()
    assert not Path(escaped).exists()
