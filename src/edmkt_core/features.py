# Ported from tcc.edm.kt @ 0e8807c — src/code_features.py
# Code feature extraction for Code-DKT (Shi et al., 2022). Numerics frozen; characterization tests gate any refactor.

#Extração de features de código para Code-DKT (Shi et al., 2022).


from __future__ import annotations

import multiprocessing as mp
import random
from typing import Optional

import numpy as np
import torch
from torch import Tensor

import javalang
from anytree import Node
from anytree.search import findall_by_attr
from anytree.walker import Walker


# ---------------------------------------------------------------------------
# Extração de paths AST — adaptado de path_extractor.py (Code-DKT)
# ---------------------------------------------------------------------------

def _get_token(node) -> str:
    if isinstance(node, str):
        return node
    if isinstance(node, set):
        return "Modifier"
    if isinstance(node, javalang.ast.Node):
        return node.__class__.__name__
    return ""


def _get_children(root) -> list:
    if isinstance(root, javalang.ast.Node):
        children = root.children
    elif isinstance(root, set):
        children = list(root)
    else:
        return []

    def expand(nested):
        for item in nested:
            if isinstance(item, list):
                yield from expand(item)
            elif item:
                yield item

    return list(expand(children))


def _build_tree(current_node, parent_node: Node, order: str) -> None:
    token = _get_token(current_node)
    children = _get_children(current_node)
    node = Node([order, token], parent=parent_node, order=order)
    for i, child in enumerate(children):
        _build_tree(child, node, order + str(i + 1))


def _parse_java(code: str):
    tokens = javalang.tokenizer.tokenize(code)
    parser = javalang.parser.Parser(tokens)
    return parser.parse_member_declaration()


def extract_paths_javalang(
    code: str,
    max_path_length: int = 8,
    max_path_width: int = 2,
    R: int = 50,
    seed: int = 42,
) -> list[tuple[str, str, str]]:

    try:
        parsed = _parse_java(code)
    except Exception:
        return []

    head = Node(["1", _get_token(parsed)])
    for i, child in enumerate(_get_children(parsed)):
        _build_tree(child, head, "1" + str(i + 1))

    leaf_nodes = findall_by_attr(head, name="is_leaf", value=True)
    if not leaf_nodes:
        return []

    #Padding dos order strings ao comprimento máximo para normalização de rank
    #(path_extractor.py: get_node_rank). O atributo .order permanece inalterado
    #e é usado na comparação de largura (get_path_width).
    max_depth = max(len(node.name[0]) for node in leaf_nodes)
    for leaf in leaf_nodes:
        while len(leaf.name[0]) < max_depth:
            leaf.name[0] += "0"
        leaf.name = [int(leaf.name[0]), leaf.name[1]]

    walker = Walker()
    paths: list[tuple[str, str, str]] = []

    for i in range(len(leaf_nodes) - 1):
        for j in range(i + 1, len(leaf_nodes)):
            try:
                upstream, lca, downstream = walker.walk(leaf_nodes[i], leaf_nodes[j])
            except Exception:
                continue

            walk_path = (
                [n.name[1] for n in upstream]
                + [lca.name[1]]
                + [n.name[1] for n in downstream]
            )

            if len(walk_path) > max_path_length:
                continue

            # Largura: diferença inteira entre orders dos nós imediatamente
            # adjacentes à LCA (path_extractor.py: get_path_width).
            # upstream[-1] = nó filho da LCA no lado de leaf_i
            # downstream[0] = nó filho da LCA no lado de leaf_j
            try:
                width = (
                    abs(int(upstream[-1].order) - int(downstream[0].order))
                    if (upstream and downstream)
                    else 0
                )
            except (ValueError, IndexError):
                continue

            if width > max_path_width:
                continue

            paths.append((walk_path[0], "@".join(walk_path), walk_path[-1]))

    if not paths:
        return []

    if len(paths) > R:
        rng = random.Random(seed)
        paths = rng.sample(paths, R)

    return paths


# ---------------------------------------------------------------------------
# Cache de paths (extração paralela)
# ---------------------------------------------------------------------------

def _worker_extract(args: tuple) -> tuple[str, list]:
    #Worker picklável para multiprocessing.Pool."""
    code_state_id, code, max_path_length, max_path_width, R, seed = args
    paths = extract_paths_javalang(code, max_path_length, max_path_width, R, seed)
    return code_state_id, paths


def build_cache(
    code_state_ids: list[str],
    code_states: dict[str, str],
    max_path_length: int = 8,
    max_path_width: int = 2,
    R: int = 50,
    seed: int = 42,
    n_workers: Optional[int] = None,
) -> dict[str, list[tuple[str, str, str]]]:
    #Extrai paths para todos os CodeStateIDs via multiprocessing.Pool.

    args_list = [
        (csid, code_states.get(csid, ""), max_path_length, max_path_width, R, seed)
        for csid in code_state_ids
    ]
    cache: dict[str, list] = {}
    with mp.Pool(n_workers) as pool:
        for csid, p in pool.imap_unordered(_worker_extract, args_list, chunksize=64):
            cache[csid] = p
    return cache


# ---------------------------------------------------------------------------
# Vocabulário
# ---------------------------------------------------------------------------

def build_vocab(
    cache_raw: dict[str, list[tuple[str, str, str]]],
) -> tuple[dict[str, int], dict[str, int]]:
    #Constrói token_to_idx e path_to_idx a partir do cache do train set.

    tokens: set[str] = set()
    path_strs: set[str] = set()
    for path_list in cache_raw.values():
        for start, path_str, end in path_list:
            tokens.add(start)
            tokens.add(end)
            path_strs.add(path_str)

    token_to_idx = {tok: idx + 1 for idx, tok in enumerate(sorted(tokens))}
    path_to_idx = {p: idx + 1 for idx, p in enumerate(sorted(path_strs))}
    return token_to_idx, path_to_idx


# ---------------------------------------------------------------------------
# Tensorização
# ---------------------------------------------------------------------------

def paths_to_tensor(
    paths: list[tuple[str, str, str]],
    token_to_idx: dict[str, int],
    path_to_idx: dict[str, int],
    R: int = 50,
) -> np.ndarray:
    #Converte lista de paths em array (R, 3) de índices com zero-padding.

    arr = np.zeros((R, 3), dtype=np.int64)
    for r, (start, path_str, end) in enumerate(paths[:R]):
        arr[r, 0] = token_to_idx.get(start, 0)
        arr[r, 1] = path_to_idx.get(path_str, 0)
        arr[r, 2] = token_to_idx.get(end, 0)
    return arr


def build_code_input_tensor(
    sequences: list[dict],
    cache_raw: dict[str, list[tuple[str, str, str]]],
    token_to_idx: dict[str, int],
    path_to_idx: dict[str, int],
    problem_to_idx: dict[int, int],
    max_len: int = 50,
    R: int = 50,
) -> tuple[Tensor, Tensor, Tensor]:
    #Constrói tensores de entrada combinados DKT one-hot + code features.

    M = len(problem_to_idx)
    N = len(sequences)

    X = torch.zeros(N, max_len, 2 * M + R * 3, dtype=torch.float32)
    Y_next = torch.zeros(N, max_len, M, dtype=torch.float32)
    mask = torch.zeros(N, max_len, dtype=torch.bool)

    for i, seq in enumerate(sequences):
        events = seq["events"]
        if len(events) > max_len:
            events = events.iloc[-max_len:]
        L = len(events)
        pad = max_len - L  # left-padding offset (readdata.py: 'extra')

        pids = events["ProblemID"].values
        corrects = events["correct"].values
        csids = events["CodeStateID"].astype(str).values

        for t_rel in range(L):
            t = pad + t_rel
            m = problem_to_idx[int(pids[t_rel])]

            # DKT one-hot (Piech et al., 2015, Section 3)
            if corrects[t_rel]:
                X[i, t, m] = 1.0
            else:
                X[i, t, m + M] = 1.0

            # Code features: lookup pré-computado → (R, 3) → flatten float32
            raw_paths = cache_raw.get(csids[t_rel], [])
            code_arr = paths_to_tensor(raw_paths, token_to_idx, path_to_idx, R)
            X[i, t, 2 * M :] = torch.from_numpy(code_arr.flatten().astype(np.float32))

            mask[i, t] = True

        # Y_next[t] = delta(q_{t+1}): one-hot do próximo problema
        for t_rel in range(L - 1):
            t = pad + t_rel
            m_next = problem_to_idx[int(pids[t_rel + 1])]
            Y_next[i, t, m_next] = 1.0

    return X, Y_next, mask
