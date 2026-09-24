"""Camada impura sobre os numerics congelados do core: cache de paths em disco (D-07/D-08)
e classificação de parse 3-vias (D-09). O `edmkt_core` é só CHAMADO, nunca alterado — todo
I/O de FS e toda a desambiguação parse-fail vs sem-paths vivem aqui (Pitfall 1).

Análogo de `ingestion/service.py` (app embrulha core puro) + `persistence/artifacts.py`
(escrita atômica write-temp-then-rename).
"""

from __future__ import annotations

import pickle
from typing import Optional

import javalang

from edmkt_core.features import build_cache, extract_paths_javalang

from edmkt_app import data_layout
from edmkt_app.values import CodeStateId, TurmaSlug

def _extract(code: str, config: dict) -> list[tuple[str, str, str]]:
    return extract_paths_javalang(
        code,
        max_path_length=config["max_path_length"],
        max_path_width=config["max_path_width"],
        R=config["R"],
        seed=config["seed"],
    )


def build_cache_on_disk(
    turma_slug: TurmaSlug,
    all_csids: list[str],
    code_states: dict[str, str],
    config: dict,
    n_workers: Optional[int] = None,
) -> dict[str, list[tuple[str, str, str]]]:
    """Cache incremental crash-safe de paths crus, namespaced por turma (D-07/D-08).

    Para cada CSID: hit no `<csid>.pkl` → carrega (pula extração); miss → coleta em
    `missing`. Chama `build_cache(missing, ...)` UMA vez (reusa o mp.Pool do core, numerics
    intactos) e grava cada resultado via `<csid>.pkl.tmp` + `.rename()` (atômico). O
    `cache_raw` combinado alimenta `build_train_vocab(cache_raw, train_csids)` — o filtro
    train-only acontece DEPOIS, então cachear todos os CSIDs globalmente NÃO vaza (CORE-04).
    """
    cache_dir = data_layout.ast_path_cache_dir(turma_slug)
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_raw: dict[str, list[tuple[str, str, str]]] = {}
    missing: list[str] = []
    for csid in all_csids:
        safe = CodeStateId(csid)
        pkl = cache_dir / f"{safe}.pkl"
        if pkl.exists():
            cache_raw[csid] = pickle.loads(pkl.read_bytes())
        else:
            missing.append(csid)

    if missing:
        fresh = build_cache(
            missing,
            code_states,
            max_path_length=config["max_path_length"],
            max_path_width=config["max_path_width"],
            R=config["R"],
            seed=config["seed"],
            n_workers=n_workers,
        )
        for csid, paths in fresh.items():
            safe = CodeStateId(csid)
            tmp = cache_dir / f"{safe}.pkl.tmp"
            tmp.write_bytes(pickle.dumps(paths))
            tmp.rename(cache_dir / f"{safe}.pkl")
            cache_raw[csid] = paths

    return cache_raw


def classify_parse(code: str, config: dict) -> str:
    """Desambigua o `[]` de `extract_paths_javalang` em 4 classes (D-09).

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
