# Taxa de parse do javalang; classifica em no_code, parse_failed, parsed_sem_paths ou com_paths.

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
    # Desambigua o `[]` de `extract_ast_paths`, replicando `_parse_java` sem importar nome privado.
    if not code.strip():
        return "no_code"
    try:
        tokens = javalang.tokenizer.tokenize(code)
        javalang.parser.Parser(tokens).parse_member_declaration()
    except Exception:
        return "parse_failed"
    return "com_paths" if _extract(code, config) else "parsed_sem_paths"


def compute_java_parse_rate(codes: list[str], config: dict) -> float:
    # Taxa honesta = (com_paths + parsed_sem_paths) / total-com-código; `no_code` sai do denominador
    classes = [classify_parse(c, config) for c in codes]
    with_code = [c for c in classes if c != "no_code"]
    if not with_code:
        return 0.0
    parsed = sum(1 for c in with_code if c in ("com_paths", "parsed_sem_paths"))
    return parsed / len(with_code)
