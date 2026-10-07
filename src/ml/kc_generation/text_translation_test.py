# O pedido da tradução dos nomes e das justificativas, numa chamada só por exercício.

from __future__ import annotations

import pytest

from ml.kc_generation.llm_client import InvalidLLMResponseError
from ml.kc_generation.text_translation import parse_translations, translate_kc_texts


class _TranslatingLLM:
    # Traduz pondo "pt " na frente de cada texto, e guarda o pedido
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, system, prompt, schema=None, validate=None) -> dict:
        self.calls.append(
            {"system": system, "prompt": prompt, "schema": schema, "validate": validate}
        )
        lines = [line for line in prompt.splitlines() if line[:1] in ("N", "R") and ": " in line]
        return {key: f"pt {text}" for key, text in (line.split(": ", 1) for line in lines)}


def test_the_request_numbers_the_names_and_the_sentences(prompt_reference_dir):
    llm = _TranslatingLLM()

    translate_kc_texts(["for loop", "string length"], ["Uses for.", "Uses length()."], llm)

    [call] = llm.calls
    reference = (prompt_reference_dir / "translation_system.txt").read_text(encoding="utf-8")
    assert call["system"] == reference
    assert call["prompt"] == (
        "# Names:\nN1: for loop\nN2: string length\n\n"
        "# Sentences:\nR1: Uses for.\nR2: Uses length().\n\n"
        "Now follow the instructions in system message and perform the task."
    )
    assert call["schema"] is None and call["validate"] is not None


def test_the_translations_come_back_in_the_same_order():
    names, reasonings = translate_kc_texts(["for loop", "while loop"], ["A.", "B."], _TranslatingLLM())

    assert names == ["pt for loop", "pt while loop"]
    assert reasonings == ["pt A.", "pt B."]


def test_a_repeated_sentence_is_sent_once_and_translated_for_every_copy():
    llm = _TranslatingLLM()

    _, reasonings = translate_kc_texts(["for loop"], ["A.", "B.", "A."], llm)

    assert "R3" not in llm.calls[0]["prompt"]
    assert reasonings == ["pt A.", "pt B.", "pt A."]


def test_nothing_to_translate_makes_no_call():
    llm = _TranslatingLLM()

    assert translate_kc_texts([], [], llm) == ([], [])
    assert llm.calls == []


@pytest.mark.parametrize(
    "response",
    [
        {},
        {"N1": "laço for"},
        {"N1": "laço for", "R1": "Usa for.", "R2": "a mais"},
        {"N1": "laço for", "R1": " "},
        {"N1": 3, "R1": "Usa for."},
    ],
    ids=["vazia", "falta_uma_frase", "texto_a_mais", "frase_em_branco", "nome_numero"],
)
def test_a_response_out_of_the_format_is_invalid(response):
    with pytest.raises(InvalidLLMResponseError):
        parse_translations(response, n_names=1, n_sentences=1)
