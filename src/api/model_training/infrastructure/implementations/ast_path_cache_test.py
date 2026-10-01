# O cache em disco reaproveita o já extraído, isola por turma e não deixa escapar um snapshot id.

from __future__ import annotations

import pickle
from pathlib import Path

import pytest

from api.model_training.infrastructure.implementations import ast_path_cache
from ml.code_dkt.ast_paths import extract_ast_paths
from ml.code_dkt.student_split import build_train_only_vocabulary
from tests.fixtures.sample_data import JAVA_LONG


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

    first = ast_path_cache.load_or_extract_ast_paths(1, 1, snapshot_ids, cache_code_states, cache_config)
    second = ast_path_cache.load_or_extract_ast_paths(1, 1, snapshot_ids, cache_code_states, cache_config)

    # A primeira chamada extrai ambos; a segunda já vê tudo em cache, sem faltar nada.
    assert sorted(calls["missing"][0]) == snapshot_ids
    assert all(len(m) == 0 for m in calls["missing"][1:])
    assert first == second


# --- namespace por turma ---------------------------------------------------


def test_each_assignment_has_its_own_cache_so_equal_ids_do_not_leak(
    java_snippets, data_root, cache_config
):
    code_a = {"shared": java_snippets.ok_a}
    code_b = {"shared": java_snippets.empty_class}  # código diferente, mesmo CSID

    # Dois envios da mesma turma, cada um num assignment
    res_a = ast_path_cache.load_or_extract_ast_paths(1, 1, ["shared"], code_a, cache_config)
    res_b = ast_path_cache.load_or_extract_ast_paths(1, 2, ["shared"], code_b, cache_config)

    versioned = data_root / "1" / "cache" / f"paths-v{ast_path_cache.AST_PATH_CACHE_VERSION}"
    file_a = versioned / "1" / "shared.pkl"
    file_b = versioned / "2" / "shared.pkl"
    assert file_a.exists() and file_b.exists()
    assert file_a != file_b
    # código com_paths gera paths; classe vazia não gera nenhum, provando que não houve sobrescrita.
    assert len(res_a["shared"]) > 0
    assert res_b["shared"] == []


# --- versão do método de extração ------------------------------------------


def test_the_cache_keeps_every_path_of_a_solution(data_root, cache_config):
    # O sorteio dos R acontece na montagem da entrada, e o vocabulário conta todos
    ast_path_cache.load_or_extract_ast_paths(1, 1, ["long"], {"long": JAVA_LONG}, cache_config)
    # A segunda chamada lê o que foi gravado no disco, e não a lista que o extrator devolveu
    reread = ast_path_cache.load_or_extract_ast_paths(
        1, 1, ["long"], {"long": JAVA_LONG}, cache_config
    )
    assert len(reread["long"]) == 142


def test_the_unversioned_cache_is_ignored_and_kept(data_root, java_snippets, cache_config):
    # O cache de antes guardava só os R sorteados, e fica no disco sem ser lido nem apagado
    old_dir = data_root / "1" / "cache" / "paths" / "1"
    old_dir.mkdir(parents=True)
    old_file = old_dir / "c1.pkl"
    old_file.write_bytes(pickle.dumps([("stale", "stale@path", "stale")]))

    paths = ast_path_cache.load_or_extract_ast_paths(
        1, 1, ["c1"], {"c1": java_snippets.ok_a}, cache_config
    )

    assert paths["c1"] == extract_ast_paths(java_snippets.ok_a)
    assert pickle.loads(old_file.read_bytes()) == [("stale", "stale@path", "stale")]


# --- classificação em 3 vias ------------------------------------------------


def test_global_cache_does_not_leak_into_train_vocab(java_snippets, data_root, cache_config):
    # Faz cache de TODOS os snapshot_ids (com_paths cada), depois monta vocab só do treino.
    code_states = {"train1": java_snippets.ok_a, "held_out": "public int z(int q) { return q * 2; }"}
    ast_paths_by_snapshot = ast_path_cache.load_or_extract_ast_paths(
        1, 1, ["train1", "held_out"], code_states, cache_config
    )
    token_to_idx, path_to_idx = build_train_only_vocabulary(ast_paths_by_snapshot, ["train1"])

    held_paths = ast_paths_by_snapshot["held_out"]
    assert held_paths, "held-out must have paths for the OOV check to be meaningful"
    oov = sum(
        1
        for start, path_str, end in held_paths
        if path_str not in path_to_idx
    )
    assert oov > 0  # paths do held-out ausentes do vocab train-only, OOV>0 comprova que não vazou


# --- guarda contra traversal --------------------------------------------------


def test_malicious_csid_cannot_escape_cache_dir(java_snippets, data_root, cache_config):
    code_states = {"../../etc/x": java_snippets.ok_a}
    with pytest.raises((ValueError, OSError)):
        ast_path_cache.load_or_extract_ast_paths(1, 1, ["../../etc/x"], code_states, cache_config)

    escaped = (data_root / ".." / ".." / "etc" / "x.pkl").resolve()
    assert not Path(escaped).exists()
