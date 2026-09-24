# AST paths, caminhos entre folhas da árvore sintática Java, feature do Code-DKT, congelada.


from __future__ import annotations

import multiprocessing as mp
import random
from typing import Optional


import javalang
from anytree import Node
from anytree.search import findall_by_attr
from anytree.walker import Walker


# Extração de paths AST, adaptado de path_extractor.py (TCC 1, Shi et al. 2022).

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


def extract_ast_paths(
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

    # Padding dos orders ao comprimento máximo antes de comparar (path_extractor.py, get_node_rank).
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

            # Largura é a diferença de order entre os filhos da LCA mais próximos de leaf_i/leaf_j.
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


# Extração em lote (paralela).

def _worker_extract(args: tuple) -> tuple[str, list]:
    # Worker picklável do multiprocessing.Pool.
    snapshot_id, code, max_path_length, max_path_width, R, seed = args
    paths = extract_ast_paths(code, max_path_length, max_path_width, R, seed)
    return snapshot_id, paths


def extract_ast_paths_for_snapshots(
    code_snapshot_ids: list[str],
    code_by_snapshot: dict[str, str],
    max_path_length: int = 8,
    max_path_width: int = 2,
    R: int = 50,
    seed: int = 42,
    n_workers: Optional[int] = None,
) -> dict[str, list[tuple[str, str, str]]]:
    # Os AST paths de cada snapshot, extraídos em paralelo (multiprocessing.Pool).

    args_list = [
        (snapshot_id, code_by_snapshot.get(snapshot_id, ""), max_path_length, max_path_width, R, seed)
        for snapshot_id in code_snapshot_ids
    ]
    cache: dict[str, list] = {}
    with mp.Pool(n_workers) as pool:
        for snapshot_id, p in pool.imap_unordered(_worker_extract, args_list, chunksize=64):
            cache[snapshot_id] = p
    return cache


# Vocabulário.

def build_ast_path_vocabulary(
    ast_paths_by_snapshot: dict[str, list[tuple[str, str, str]]],
) -> tuple[dict[str, int], dict[str, int]]:
    # token_to_idx e path_to_idx a partir dos paths recebidos (quem chama passa só o treino).

    tokens: set[str] = set()
    path_strs: set[str] = set()
    for path_list in ast_paths_by_snapshot.values():
        for start, path_str, end in path_list:
            tokens.add(start)
            tokens.add(end)
            path_strs.add(path_str)

    token_to_idx = {tok: idx + 1 for idx, tok in enumerate(sorted(tokens))}
    path_to_idx = {p: idx + 1 for idx, p in enumerate(sorted(path_strs))}
    return token_to_idx, path_to_idx
