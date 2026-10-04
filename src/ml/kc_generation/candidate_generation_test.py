# O prompt de geração igual ao do repositório do Duan e a leitura da resposta no formato dele.

from __future__ import annotations

import json

import pytest

from ml.kc_generation.candidate_generation import generate_candidate_kcs, parse_candidate_kcs
from ml.kc_generation.llm_client import InvalidLLMResponseError

_ANSWER = {
    "KC 1": {"reasoning": "Both solutions add the two ints.", "name": "Integer addition"},
    "KC 2": {"reasoning": "Both solutions test a closed range.", "name": "Range check"},
}


class _RecordingLLM:
    # Guarda o que recebeu e devolve uma resposta fixa, sem chamar o modelo
    def __init__(self, answer: dict) -> None:
        self.answer = answer
        self.calls: list[dict] = []

    def generate(self, system, prompt, schema=None, validate=None) -> dict:
        self.calls.append({"system": system, "prompt": prompt, "schema": schema, "validate": validate})
        return self.answer


def _reference(prompt_reference_dir, name: str) -> str:
    return (prompt_reference_dir / name).read_text(encoding="utf-8")


def _input(prompt_reference_dir) -> dict:
    return json.loads(_reference(prompt_reference_dir, "generation_input.json"))


def test_the_prompt_with_a_statement_is_the_one_of_the_repository(prompt_reference_dir):
    data = _input(prompt_reference_dir)
    llm = _RecordingLLM(_ANSWER)

    generate_candidate_kcs(data["solutions"], data["statement"], llm)

    [call] = llm.calls
    assert call["system"] == _reference(prompt_reference_dir, "generation_system.txt")
    assert call["prompt"] == _reference(prompt_reference_dir, "generation_user_with_statement.txt")


def test_without_a_statement_only_the_two_statement_lines_leave(prompt_reference_dir):
    data = _input(prompt_reference_dir)
    llm = _RecordingLLM(_ANSWER)

    generate_candidate_kcs(data["solutions"], None, llm)

    [call] = llm.calls
    assert call["system"] == _reference(prompt_reference_dir, "generation_system.txt")
    assert call["prompt"] == _reference(
        prompt_reference_dir, "generation_user_without_statement.txt"
    )


def test_the_call_goes_without_a_schema_and_with_the_validation(prompt_reference_dir):
    # O prompt do Duan pede o JSON no texto, então a CLI não recebe schema
    llm = _RecordingLLM(_ANSWER)

    generate_candidate_kcs(["int f() { return 1; }"], None, llm)

    [call] = llm.calls
    assert call["schema"] is None
    assert call["validate"] is parse_candidate_kcs


@pytest.mark.parametrize("n_solutions", [1, 3, 5])
def test_the_system_text_counts_the_solutions(n_solutions):
    llm = _RecordingLLM(_ANSWER)

    generate_candidate_kcs([f"int f{i}() {{ return {i}; }}" for i in range(n_solutions)], None, llm)

    [call] = llm.calls
    assert f"along with {n_solutions} sample solutions." in call["system"]


def test_the_candidates_keep_the_order_of_the_answer():
    llm = _RecordingLLM(_ANSWER)

    candidates = generate_candidate_kcs(["int f() { return 1; }"], None, llm)

    assert candidates == [
        {"name": "Integer addition", "reasoning": "Both solutions add the two ints."},
        {"name": "Range check", "reasoning": "Both solutions test a closed range."},
    ]


@pytest.mark.parametrize(
    "response",
    [
        {},
        [],
        {"KC 1": "Integer addition"},
        {"KC 1": {"reasoning": "x"}},
        {"KC 1": {"name": "Integer addition"}},
        {"KC 1": {"reasoning": " ", "name": "Integer addition"}},
        {"KC 1": {"reasoning": "x", "name": ""}},
        {"KC 1": {"reasoning": "x", "name": "   "}},
        {"KC 1": {"reasoning": "x", "name": 3}},
        {"KC 1": {"reasoning": "x", "name": "ok"}, "analysis": "texto solto"},
    ],
    ids=[
        "vazia",
        "lista",
        "kc_sem_objeto",
        "sem_nome",
        "sem_justificativa",
        "justificativa_em_branco",
        "nome_vazio",
        "nome_em_branco",
        "nome_numero",
        "chave_a_mais",
    ],
)
def test_a_response_out_of_the_format_is_invalid(response):
    with pytest.raises(InvalidLLMResponseError):
        parse_candidate_kcs(response)
