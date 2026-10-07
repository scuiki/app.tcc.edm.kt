# Fixtures dos testes de knowledge_components.

from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd
import pytest

_NAMING_OPENING = "The knowledge components list is: "
_EVIDENCE_OPENING = "# Knowledge components:\n"
_TRANSLATION_OPENING = "# Names:\n"


def fake_embed(codes: list[str]) -> np.ndarray:
    # Vetores falsos no lugar do CodeBERT e do SBERT, um por texto, sem carregar o modelo
    return np.array([[len(code), sum(map(ord, code)) % 97 + 1, 1.0] for code in codes])


def naming_answer(prompt: str) -> dict | None:
    # Para o pedido de nomeação, a resposta da Tabela 10 com o primeiro KC da lista, e senão None
    if not prompt.startswith(_NAMING_OPENING):
        return None
    names = json.loads(prompt[len(_NAMING_OPENING) :].split("\n", 1)[0])
    return {
        "reasoning": "One KC covers the others.",
        "representative kc": names[0],
        "summary name": None,
    }


def evidence_answer(prompt: str) -> dict | None:
    # Para o pedido dos trechos, a primeira linha da solução 1 em cada conceito, e senão None
    if not prompt.startswith(_EVIDENCE_OPENING):
        return None
    first_line = prompt.split("## Sample solution 1:\n", 1)[1].split("\n", 1)[0]
    concepts = re.findall(r"^KC (\d+): ", prompt, flags=re.MULTILINE)
    return {f"KC {i}": {"solution": 1, "snippet": first_line} for i in concepts}


def translation_answer(prompt: str) -> dict | None:
    # Para o pedido da tradução, cada texto com "pt " na frente, e senão None
    if not prompt.startswith(_TRANSLATION_OPENING):
        return None
    texts = re.findall(r"^([NR]\d+): (.*)$", prompt, flags=re.MULTILINE)
    return {key: f"pt {text}" for key, text in texts}


def stage_answer(prompt: str) -> dict | None:
    # A resposta falsa da nomeação, dos trechos ou da tradução, e None para o pedido de geração
    for answer in (naming_answer, evidence_answer, translation_answer):
        result = answer(prompt)
        if result is not None:
            return result
    return None


# As marcas que o LLM falso dos trechos procura no código, uma por conceito
FOR_MARK = "for ("
LENGTH_MARK = ".length()"


def multiline_code(problem: int, variant: int) -> str:
    # Código de várias linhas com CRLF, como o dado real, com cada marca numa linha só
    pad = [f"    int pad{problem}_{variant}_{k} = {k};" for k in range(variant % 4)]
    even = variant % 2 == 0
    body = [
        f"public int p{problem}v{variant}(String s) {{",
        *pad,
        "    int total = 0;",
        f"    for (int i = 0; i < {variant + 2}; i++) {{" if even else f"    total = {variant};",
        "        total += i;" if even else "    total = total + 1;",
        "    }" if even else "    total = total * 2;",
        "    return total + s.length();" if variant % 3 != 0 else "    return s.length();",
        "}",
    ]
    return "\r\n".join(body)


def multiline_runs(problem_ids: list[int], per_problem: int = 7) -> pd.DataFrame:
    # Execuções corretas com o código de várias linhas, todas distintas
    rows = [
        {
            "submission_id": problem * 100 + variant,
            "student_id": f"S{variant}",
            "problem_id": problem,
            "code_snapshot_id": f"c{problem}_{variant}",
            "code": multiline_code(problem, variant),
            "submitted_at": pd.Timestamp("2026-01-01T00:00:00Z") + pd.Timedelta(minutes=variant),
        }
        for problem in problem_ids
        for variant in range(per_problem)
    ]
    return pd.DataFrame(rows)


def evidence_solutions(prompt: str) -> list[str]:
    # As soluções do pedido dos trechos, entre a lista de conceitos e a frase de fecho
    section = prompt.split("\n\n", 1)[1].rsplit("\n\nNow follow the instructions", 1)[0]
    return re.split(r"(?:^|\n)## Sample solution \d+:\n", section)[1:]


def evidence_concepts(prompt: str) -> list[str]:
    return re.findall(r"^KC \d+: (.*)$", prompt.split("\n\n", 1)[0], flags=re.MULTILINE)


class MarkedCodeLLM:
    # LLM falso que aponta, para cada conceito, a última solução com a marca e as duas linhas dela
    def __init__(self, names_by_problem: dict[int, list[str]]) -> None:
        self.names = names_by_problem
        self.evidence_prompts: list[str] = []
        self.translation_prompts: list[str] = []

    def generate(self, system: str, prompt: str, schema=None, validate=None) -> dict:
        naming = naming_answer(prompt)
        if naming is not None:
            return naming
        if prompt.startswith(_TRANSLATION_OPENING):
            self.translation_prompts.append(prompt)
            return translation_answer(prompt)
        if prompt.startswith(_EVIDENCE_OPENING):
            self.evidence_prompts.append(prompt)
            return self._evidence(prompt)
        problem = int(re.search(r"public int p(\d+)v", prompt).group(1))
        return {
            f"KC {i}": {"reasoning": f"why {name} in {problem}", "name": name}
            for i, name in enumerate(self.names[problem], 1)
        }

    @staticmethod
    def _evidence(prompt: str) -> dict:
        solutions = evidence_solutions(prompt)
        answer = {}
        for i, concept in enumerate(evidence_concepts(prompt), 1):
            mark = FOR_MARK if concept == "for loop" else LENGTH_MARK
            position = max(k for k, code in enumerate(solutions, 1) if mark in code)
            lines = solutions[position - 1].split("\r\n")
            first = next(j for j, line in enumerate(lines) if mark in line)
            # O LLM real muda o recuo ao copiar, então o trecho vai sem recuo e com quebra simples
            snippet = "\n".join(line.strip() for line in lines[first : first + 2])
            answer[f"KC {i}"] = {"solution": position, "snippet": snippet}
        return answer


@pytest.fixture
def fake_claude_envelope():
    # O JSON que `claude -p --output-format json` devolve, para os testes nunca chamarem o binário
    def build(structured_output, result: str = "") -> dict:
        return {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": result,
            "structured_output": structured_output,
        }

    return build
