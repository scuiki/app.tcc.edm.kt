# O pedido dos trechos de cada conceito e a procura de cada trecho na solução.

from __future__ import annotations

import pytest

from ml.kc_generation.evidence_location import (
    find_snippet_lines,
    locate_kc_evidence,
    parse_kc_evidence,
)
from ml.kc_generation.llm_client import InvalidLLMResponseError

_SOLUTIONS = [
    "public int sortaSum(int a, int b)\n{\n    int sum = a + b;\n    if (sum >= 10 && sum <= 19)\n"
    "        return 20;\n    return sum;\n}",
    "public int sortaSum(int a, int b) {\n  return (a + b >= 10 && a + b <= 19) ? 20 : a + b;\n}",
]


class _RecordingLLM:
    # Guarda o que recebeu e devolve uma resposta fixa, sem chamar o modelo
    def __init__(self, answer: dict) -> None:
        self.answer = answer
        self.calls: list[dict] = []

    def generate(self, system, prompt, schema=None, validate=None) -> dict:
        self.calls.append(
            {"system": system, "prompt": prompt, "schema": schema, "validate": validate}
        )
        return self.answer


def test_the_request_numbers_the_concepts_and_the_solutions(prompt_reference_dir):
    llm = _RecordingLLM({"KC 1": {"solution": None, "snippet": None}})

    locate_kc_evidence(["integer addition"], _SOLUTIONS, llm)

    [call] = llm.calls
    reference = (prompt_reference_dir / "evidence_system.txt").read_text(encoding="utf-8")
    assert call["system"] == reference
    # As soluções vão numeradas como no prompt de geração, então a posição é a da amostra
    assert call["prompt"] == (
        "# Knowledge components:\nKC 1: integer addition\n\n"
        f"## Sample solution 1:\n{_SOLUTIONS[0]}\n## Sample solution 2:\n{_SOLUTIONS[1]}\n\n"
        "Now follow the instructions in system message and perform the task."
    )
    assert call["schema"] is None and call["validate"] is not None


def test_each_concept_gets_the_lines_of_its_snippet_or_none():
    answer = {
        "KC 1": {"solution": 1, "snippet": "int sum = a + b;"},
        "KC 2": {"solution": 2, "snippet": "return (a + b >= 10 && a + b <= 19) ? 20 : a + b;"},
        "KC 3": {"solution": None, "snippet": None},
        # Um trecho que não está na solução é descartado, e o conceito fica sem trecho
        "KC 4": {"solution": 1, "snippet": "while (sum > 0)"},
    }

    located = locate_kc_evidence(["a", "b", "c", "d"], _SOLUTIONS, _RecordingLLM(answer))

    assert located == [(1, 3, 3), (2, 2, 2), None, None]


@pytest.mark.parametrize(
    ("snippet", "lines"),
    [
        ("int sum = a + b;", (3, 3)),
        ("if (sum >= 10 && sum <= 19)\nreturn 20;", (4, 5)),
        ("sum >= 10 && sum <= 19", (4, 4)),
        ("    return sum;\n}", (6, 7)),
        ("return sum ;", None),
        ("   ", None),
    ],
    ids=["linha", "duas_linhas_com_outro_recuo", "pedaco_de_linha", "ate_o_fim", "outro_codigo", "vazio"],
)
def test_the_snippet_is_found_whatever_the_spaces(snippet, lines):
    assert find_snippet_lines(_SOLUTIONS[0], snippet) == lines


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"KC 1": {"solution": 1, "snippet": "x"}},
        {"KC 1": {"solution": 1, "snippet": "x"}, "KC 2": {"solution": 1, "snippet": "y"}, "KC 3": {}},
        {"KC 1": {"solution": 3, "snippet": "x"}, "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": {"solution": 0, "snippet": "x"}, "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": {"solution": True, "snippet": "x"}, "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": {"solution": 1, "snippet": " "}, "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": {"solution": 1, "snippet": None}, "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": {"solution": None, "snippet": "x"}, "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": "x", "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": {}, "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": {"solution": None}, "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": {"reasoning": "x", "name": "y"}, "KC 2": {"solution": None, "snippet": None}},
        {"KC 1": {"solution": 1, "snippet": "x"}, "KC 3": {"solution": 1, "snippet": "y"}},
    ],
    ids=[
        "vazia",
        "falta_um_conceito",
        "conceito_a_mais",
        "solucao_que_nao_existe",
        "solucao_zero",
        "solucao_booleana",
        "trecho_em_branco",
        "solucao_sem_trecho",
        "trecho_sem_solucao",
        "item_sem_objeto",
        "item_vazio",
        "so_a_solucao_nula",
        "item_de_outro_prompt",
        "chave_de_outro_numero",
    ],
)
def test_a_response_out_of_the_format_is_invalid(response):
    with pytest.raises(InvalidLLMResponseError):
        parse_kc_evidence(response, n_concepts=2, n_solutions=2)


def test_a_snippet_that_appears_twice_gets_its_first_occurrence():
    code = "int f() {\r\n    return x;\r\n}\r\nint g() {\r\n    return x;\r\n}"
    assert find_snippet_lines(code, "return x;") == (2, 2)


def test_crlf_and_lf_give_the_same_lines_up_to_the_end_of_the_code():
    lf = "if (a)\n    return 1;\nreturn 2;"
    crlf = lf.replace("\n", "\r\n")
    assert find_snippet_lines(lf, "return 2;") == find_snippet_lines(crlf, "return 2;") == (3, 3)
    assert find_snippet_lines(crlf, "if (a) return 1;") == (1, 2)


def test_regex_characters_in_the_snippet_are_taken_literally():
    code = "x[i] += (a*b) ? c : d;\r\nint[] y = new int[n + 1];"
    assert find_snippet_lines(code, "x[i] += (a*b) ? c : d;") == (1, 1)
    assert find_snippet_lines(code, "new int[n + 1];") == (2, 2)
