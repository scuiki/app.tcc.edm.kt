# Etapa 6 do KCGen-KT, pede ao LLM onde cada conceito do problema aparece nas soluções que ele leu.

from __future__ import annotations

import re

from ml.kc_generation.llm_client import InvalidLLMResponseError, LLMClient

# O prompt é do app, no formato dos prompts do Duan, e não muda o método
_SYSTEM = """You are an experienced computer science teacher and education expert. You are given the numbered sample solutions of a Java programming problem and the numbered knowledge components (KCs) that the problem requires. Your task is to point out where each KC appears in the solutions.

Please follow these steps:
1. For each KC, choose the sample solution that shows it most clearly.
2. Copy from that solution the shortest snippet of one or more complete, consecutive lines that shows the KC, exactly as it is written, without changing, omitting or adding any character.
3. If a KC does not appear in any of the solutions, use null for both the solution and the snippet.

Your final response must strictly follow this JSON template, with one entry for each KC:
{
    "KC 1": {"solution": 2, "snippet": "Lines copied from sample solution 2"},
    "KC 2": {"solution": 1, "snippet": "Lines copied from sample solution 1"},
    ...
}"""

_CLOSING = "Now follow the instructions in system message and perform the task."


def _user_prompt(concepts: list[str], solutions: list[str]) -> str:
    # As soluções vão numeradas como no prompt de geração, e a posição delas é a da amostra
    return (
        "# Knowledge components:\n"
        + "\n".join(f"KC {i}: {name}" for i, name in enumerate(concepts, 1))
        + "\n\n"
        + "\n".join(f"## Sample solution {i}:\n{code}" for i, code in enumerate(solutions, 1))
        + "\n\n"
        + _CLOSING
    )


def parse_kc_evidence(
    response: dict, n_concepts: int, n_solutions: int
) -> list[tuple[int, str] | None]:
    # Para cada conceito, na ordem, a solução e o trecho, ou None quando o LLM não o achou
    expected = [f"KC {i}" for i in range(1, n_concepts + 1)]
    if not isinstance(response, dict) or sorted(response) != sorted(expected):
        raise InvalidLLMResponseError("a resposta não traz um item para cada conceito")
    found: list[tuple[int, str] | None] = []
    for key in expected:
        item = response[key]
        solution = item.get("solution") if isinstance(item, dict) else None
        snippet = item.get("snippet") if isinstance(item, dict) else None
        both_keys = isinstance(item, dict) and "solution" in item and "snippet" in item
        if both_keys and solution is None and snippet is None:
            found.append(None)
            continue
        if not isinstance(solution, int) or isinstance(solution, bool):
            raise InvalidLLMResponseError(f"{key} veio sem o número da solução")
        if not 1 <= solution <= n_solutions:
            raise InvalidLLMResponseError(f"{key} aponta uma solução que não existe")
        if not isinstance(snippet, str) or not snippet.strip():
            raise InvalidLLMResponseError(f"{key} veio sem o trecho")
        found.append((solution, snippet))
    return found


def find_snippet_lines(code: str, snippet: str) -> tuple[int, int] | None:
    # A primeira e a última linha do trecho no código, sem contar as diferenças de espaço
    tokens = snippet.split()
    if not tokens:
        return None
    match = re.search(r"\s+".join(re.escape(token) for token in tokens), code)
    if match is None:
        return None
    return code.count("\n", 0, match.start()) + 1, code.count("\n", 0, match.end()) + 1


def locate_kc_evidence(
    concepts: list[str], solutions: list[str], llm: LLMClient
) -> list[tuple[int, int, int] | None]:
    # Para cada conceito, a posição da solução e as linhas do trecho, ou None sem trecho que exista
    def validate(response: dict) -> None:
        parse_kc_evidence(response, len(concepts), len(solutions))

    response = llm.generate(_SYSTEM, _user_prompt(concepts, solutions), validate=validate)
    located: list[tuple[int, int, int] | None] = []
    for item in parse_kc_evidence(response, len(concepts), len(solutions)):
        lines = None if item is None else find_snippet_lines(solutions[item[0] - 1], item[1])
        located.append(None if lines is None else (item[0], *lines))
    return located
