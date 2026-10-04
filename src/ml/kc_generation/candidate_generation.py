# Etapa 2 do KCGen-KT, pede ao LLM os KCs de cada problema com o prompt do repositório do Duan.

from __future__ import annotations

from ml.kc_generation.llm_client import InvalidLLMResponseError, LLMClient

# Os dois exemplos do repositório, com o enunciado e as tags da planilha oficial já convertidas
_EXAMPLES: dict[str, list[str]] = {
    "Write a function in Java that implements the following logic: Given a string str and a non-empty word, return a version of the original string where all chars have been replaced by pluses (+), except for appearances of the word which are preserved unchanged.": [
        "If and else statement",
        "While loop",
        "Numerical comparisons",
        "String formatting",
        "String concatenation",
        "String indexing",
        "String length",
        "String equality comparison",
    ],
    "Write a function in Java that implements the following logic: You are driving a little too fast, and a police officer stops you. Write code to compute the result, encoded as an int value: 0=no ticket, 1=small ticket, or 2=big ticket. If speed is 60 or less, the result is 0. If speed is between 61 and 80 inclusive, the result is 1. If speed is 81 or more, the result is 2. Unless it is your birthday--on that day, your speed can be 5 higher in all cases.": [
        "If and else statement",
        "Nested if statement",
        "Basic arithmetic operations",
        "Logical operators",
        "Numerical comparisons",
        "Boolean operations",
    ],
}

# O texto de sistema do repositório com Java no lugar da linguagem, e a linha só com espaço é dele
_SYSTEM_TEMPLATE = """You are an experienced computer science teacher and education expert. You are given a Java programming problem along with {n_solutions} sample solutions. Your task is to identify generalizable knowledge components (skills or concepts) necessary to solve such problems.

A knowledge component (KC) is a single, reusable unit of programming understanding, such as a language construct, pattern, or skill, that contributes to solving a programming problem and can be learned or mastered independently.

Please follow these steps:
1. Analyze each solution carefully, noting critical constructs.
2. Reflect step by step on how each solution maps to distinct programming KCs that are independent and reusable.
3. For each KC, generate a concise name and provide a one-sentence reasoning explaining why this KC is necessary based on the provided solutions. Use the provided examples as reference for the appropriate level of detail. Make sure KCs are generalizable and applicable to a wide range of similar programming problems without referencing problem-specific details.
4. Ensure each KC is atomic and not bundled with others.
\x20

Your final response must strictly follow this JSON template:
{{
    "KC 1": {{"reasoning": "Reasoning for this KC (exactly 1 sentence)", "name": "Knowledge component name"}},
    "KC 2": {{"reasoning": "Reasoning for this KC (exactly 1 sentence)", "name": "Another specific knowledge component name"}},
    ...
}}"""

_CLOSING = "Follow the instructions in system message. First, carefully examine the solutions and identify the important elements and patterns. Then, explicitly reason about what underlying knowledge components are required based on these solution codes. Finally, take the examples as reference and summarize your analysis clearly into generalizable and concise knowledge components."


def _examples_block() -> str:
    # A montagem dos exemplos do repositório, com os KCs de cada um num JSON
    exam_prompt = ""
    for idx, (problem, kc_list) in enumerate(_EXAMPLES.items(), 1):
        kc_json = {f"KC {i+1}": kc for i, kc in enumerate(kc_list)}
        kc_str = ",\n  ".join([f'"{k}": "{v}"' for k, v in kc_json.items()])
        example_block = f"""# Example {idx}:
## Problem:
{problem}

## Expected KCs:
{{
  {kc_str}
}}

"""
        exam_prompt += example_block
    return exam_prompt


def _user_prompt(solutions: list[str], statement: str | None) -> str:
    # Sem enunciado, só as duas linhas do enunciado do problema saem, e o resto fica igual
    problem = f"# Problem:\n{statement}\n" if statement else ""
    return (
        _examples_block()
        + "Now analyze the following problem using their solution code. \n"
        + problem
        + "\n"
        + "\n".join([f"## Sample solution {i+1}:\n{sol}" for i, sol in enumerate(solutions)])
        + "\n\n"
        + _CLOSING
    )


def parse_candidate_kcs(response: dict) -> list[dict[str, str]]:
    # Um objeto por KC com a justificativa e o nome, na ordem da resposta, ou a resposta é inválida
    if not isinstance(response, dict) or not response:
        raise InvalidLLMResponseError("a resposta não trouxe nenhum KC")
    candidates = []
    for key, kc in response.items():
        name = kc.get("name") if isinstance(kc, dict) else None
        reasoning = kc.get("reasoning") if isinstance(kc, dict) else None
        if not isinstance(name, str) or not name.strip():
            raise InvalidLLMResponseError(f"{key} veio sem nome")
        if not isinstance(reasoning, str) or not reasoning.strip():
            raise InvalidLLMResponseError(f"{key} veio sem justificativa")
        candidates.append({"name": name, "reasoning": reasoning})
    return candidates


def generate_candidate_kcs(
    solutions: list[str], statement: str | None, llm: LLMClient
) -> list[dict[str, str]]:
    # O LLM lê o código Java cru, porque na Tabela 4 de Duan et al. (2026) a AST piora o AUC
    response = llm.generate(
        _SYSTEM_TEMPLATE.format(n_solutions=len(solutions)),
        _user_prompt(solutions, statement),
        validate=parse_candidate_kcs,
    )
    return parse_candidate_kcs(response)
