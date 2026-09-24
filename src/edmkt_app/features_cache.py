"""Camada impura sobre os numerics congelados do core: cache de paths em disco (D-07/D-08)
e classificação de parse 3-vias (D-09). O `ml` é só CHAMADO, nunca alterado — todo
I/O de FS e toda a desambiguação parse-fail vs sem-paths vivem aqui (Pitfall 1).

Análogo de `ingestion/service.py` (app embrulha core puro) + `persistence/artifacts.py`
(escrita atômica write-temp-then-rename).
"""

from __future__ import annotations

import pickle
from typing import Optional

import javalang

from ml.code_dkt.ast_paths import extract_ast_paths, extract_ast_paths_for_snapshots

from edmkt_app import data_layout
from edmkt_app.values import CodeStateId, TurmaSlug

def _extract(code: str, config: dict) -> list[tuple[str, str, str]]:
    return extract_ast_paths(
        code,
        max_path_length=config["max_path_length"],
        max_path_width=config["max_path_width"],
        R=config["R"],
        seed=config["seed"],
    )


def build_cache_on_disk(
    turma_slug: TurmaSlug,
    all_snapshot_ids: list[str],
    code_states: dict[str, str],
    config: dict,
    n_workers: Optional[int] = None,
) -> dict[str, list[tuple[str, str, str]]]:
    """Cache incremental crash-safe de paths crus, namespaced por turma (D-07/D-08).

    Para cada CSID: hit no `<snapshot_id>.pkl` → carrega (pula extração); miss → coleta em
    `missing`. Chama `extract_ast_paths_for_snapshots(missing, ...)` UMA vez (reusa o mp.Pool do core, numerics
    intactos) e grava cada resultado via `<snapshot_id>.pkl.tmp` + `.rename()` (atômico). O
    `ast_paths_by_snapshot` combinado alimenta `build_train_only_vocabulary(ast_paths_by_snapshot, train_snapshot_ids)` — o filtro
    train-only acontece DEPOIS, então cachear todos os CSIDs globalmente NÃO vaza (CORE-04).
    """
    cache_dir = data_layout.ast_path_cache_dir(turma_slug)
    cache_dir.mkdir(parents=True, exist_ok=True)

    ast_paths_by_snapshot: dict[str, list[tuple[str, str, str]]] = {}
    missing: list[str] = []
    for snapshot_id in all_snapshot_ids:
        safe = CodeStateId(snapshot_id)
        pkl = cache_dir / f"{safe}.pkl"
        if pkl.exists():
            ast_paths_by_snapshot[snapshot_id] = pickle.loads(pkl.read_bytes())
        else:
            missing.append(snapshot_id)

    if missing:
        fresh = extract_ast_paths_for_snapshots(
            missing,
            code_states,
            max_path_length=config["max_path_length"],
            max_path_width=config["max_path_width"],
            R=config["R"],
            seed=config["seed"],
            n_workers=n_workers,
        )
        for snapshot_id, paths in fresh.items():
            safe = CodeStateId(snapshot_id)
            tmp = cache_dir / f"{safe}.pkl.tmp"
            tmp.write_bytes(pickle.dumps(paths))
            tmp.rename(cache_dir / f"{safe}.pkl")
            ast_paths_by_snapshot[snapshot_id] = paths

    return ast_paths_by_snapshot


def classify_parse(code: str, config: dict) -> str:
    """Desambigua o `[]` de `extract_ast_paths` em 4 classes (D-09).

    O core retorna `[]` tanto para parse-fail (features.py:92) quanto para parseado-sem-paths
    (features.py:100/149). Para separar, replicamos as 3 linhas de `_parse_java` aqui em vez de
    importar o nome privado — mantém a superfície pública do core inalterada (RESEARCH Pattern 5).
    """
    if not code.strip():
        return "no_code"
    try:
        tokens = javalang.tokenizer.tokenize(code)
        javalang.parser.Parser(tokens).parse_member_declaration()
    except Exception:
        return "parse_failed"
    return "com_paths" if _extract(code, config) else "parsed_sem_paths"


def parse_rate(codes: list[str], config: dict) -> float:
    """Taxa de parse honesta = (com_paths + parsed_sem_paths) / total-com-código (D-09).

    `no_code` sai do denominador (sem snapshot, não é falha de parse). Denominador 0 → 0.0.
    """
    classes = [classify_parse(c, config) for c in codes]
    with_code = [c for c in classes if c != "no_code"]
    if not with_code:
        return 0.0
    parsed = sum(1 for c in with_code if c in ("com_paths", "parsed_sem_paths"))
    return parsed / len(with_code)
