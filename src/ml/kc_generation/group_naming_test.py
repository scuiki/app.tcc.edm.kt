# O prompt de nomeação igual ao texto da Tabela 10 e a leitura do nome do grupo na resposta.

from __future__ import annotations

import json

import pytest

from ml.kc_generation.group_naming import name_kc_group, parse_group_name
from ml.kc_generation.llm_client import InvalidLLMResponseError


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


_REPRESENTATIVE = {
    "reasoning": "One KC covers the others.",
    "representative kc": "While loop",
    "summary name": None,
}


def test_the_naming_prompt_is_the_one_of_table_10(prompt_reference_dir):
    names = json.loads((prompt_reference_dir / "naming_input.json").read_text(encoding="utf-8"))[
        "names"
    ]
    llm = _RecordingLLM(_REPRESENTATIVE)

    name_kc_group(names, llm)

    [call] = llm.calls
    assert call["system"] == (prompt_reference_dir / "naming_system.txt").read_text(encoding="utf-8")
    assert call["prompt"] == (prompt_reference_dir / "naming_user.txt").read_text(encoding="utf-8")
    # O prompt pede o JSON no texto, então a CLI não recebe schema, e a resposta é validada
    assert call["schema"] is None
    assert call["validate"] is parse_group_name


def test_the_name_is_the_representative_in_lowercase():
    assert name_kc_group(["while loop", "for loop"], _RecordingLLM(_REPRESENTATIVE)) == "while loop"


def test_without_a_representative_the_name_is_the_summary_in_lowercase():
    answer = {"reasoning": "They differ.", "representative kc": None, "summary name": "Loop Constructs"}
    assert name_kc_group(["while loop", "for loop"], _RecordingLLM(answer)) == "loop constructs"


@pytest.mark.parametrize(
    "response",
    [
        {},
        [],
        {"representative kc": "While loop", "summary name": None},
        {"reasoning": " ", "representative kc": "While loop", "summary name": None},
        {"reasoning": "x", "representative kc": None, "summary name": None},
        {"reasoning": "x", "representative kc": "", "summary name": "Loops"},
        {"reasoning": "x", "representative_kc": "While loop", "summary_name": None},
    ],
    ids=[
        "vazia",
        "lista",
        "sem_justificativa",
        "justificativa_em_branco",
        "os_dois_nulos",
        "representante_vazio",
        "chaves_do_repositorio",
    ],
)
def test_a_response_out_of_the_format_is_invalid(response):
    with pytest.raises(InvalidLLMResponseError):
        parse_group_name(response)


def test_the_representative_wins_over_the_summary_when_both_come():
    answer = {"reasoning": "x", "representative kc": "While loop", "summary name": "Loops"}
    assert parse_group_name(answer) == "while loop"


@pytest.mark.parametrize(
    "response",
    [
        {"reasoning": "x", "representative kc": " ", "summary name": None},
        {"reasoning": "x", "representative kc": None, "summary name": "  "},
        {"reasoning": "x", "representative kc": 3, "summary name": "Loops"},
        {"reasoning": "x", "representative kc": None, "summary name": 3},
    ],
    ids=[
        "representante_em_branco",
        "resumo_em_branco",
        "representante_numero",
        "resumo_numero",
    ],
)
def test_a_blank_or_non_text_name_is_invalid(response):
    with pytest.raises(InvalidLLMResponseError):
        parse_group_name(response)


def test_the_list_goes_as_the_json_dumps_of_the_repository():
    # O `json.dumps` padrão escapa o que não é ASCII, como o repositório manda a lista
    llm = _RecordingLLM(_REPRESENTATIVE)

    name_kc_group(["laço while", "for loop"], llm)

    [call] = llm.calls
    expected = 'The knowledge components list is: ["la\\u00e7o while", "for loop"]\n'
    assert call["prompt"].startswith(expected)
