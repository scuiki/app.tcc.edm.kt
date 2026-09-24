"""A taxa de parse do javalang: quanto do código dos alunos o Code-DKT de fato enxerga.

O ml/ devolve `[]` tanto para "não parseou" quanto para "parseou mas não tem path", então a
classificação em quatro casos mora aqui: no_code, parse_failed, parsed_sem_paths, com_paths.
"""

from __future__ import annotations

import javalang

from ml.code_dkt.ast_paths import extract_ast_paths


def _extract(code: str, config: dict) -> list[tuple[str, str, str]]:
    return extract_ast_paths(
        code,
        max_path_length=config["max_path_length"],
        max_path_width=config["max_path_width"],
        R=config["R"],
        seed=config["seed"],
    )


def classify_parse(code: str, config: dict) -> str:
    """Desambigua o `[]` de `extract_ast_paths` em 4 classes.

    O core retorna `[]` tanto para parse-fail quanto para parseado-sem-paths
   . Para separar, replicamos as 3 linhas de `_parse_java` aqui em vez de
    importar o nome privado — mantém a superfície pública do core inalterada.
    """
    if not code.strip():
        return "no_code"
    try:
        tokens = javalang.tokenizer.tokenize(code)
        javalang.parser.Parser(tokens).parse_member_declaration()
    except Exception:
        return "parse_failed"
    return "com_paths" if _extract(code, config) else "parsed_sem_paths"


def compute_java_parse_rate(codes: list[str], config: dict) -> float:
    """Taxa de parse honesta = (com_paths + parsed_sem_paths) / total-com-código.

    `no_code` sai do denominador (sem snapshot, não é falha de parse). Denominador 0 → 0.0.
    """
    classes = [classify_parse(c, config) for c in codes]
    with_code = [c for c in classes if c != "no_code"]
    if not with_code:
        return 0.0
    parsed = sum(1 for c in with_code if c in ("com_paths", "parsed_sem_paths"))
    return parsed / len(with_code)
