# Etapa 7 do KCGen-KT, pede ao LLM o português dos nomes e das justificativas do exercício.

from __future__ import annotations

from ml.kc_generation.llm_client import InvalidLLMResponseError, LLMClient

# O prompt é do app, no formato dos prompts do Duan, e roda depois do método, que é em inglês
_SYSTEM = """You are an experienced computer science teacher and education expert who translates teaching material from English to Brazilian Portuguese. You are given the names of the knowledge components (KCs) of a Java programming exercise, numbered N1, N2 and so on, and the sentences that explain why each KC is needed, numbered R1, R2 and so on.

Please follow these steps:
1. Translate every name and every sentence to Brazilian Portuguese.
2. Keep Java keywords, operators, types, method names and any code exactly as they are, such as for, while, if, &&, int, String and length().
3. Translate each name as a topic name, the way a teacher would write it in a course syllabus, keeping all of its meaning, with only the first letter capitalized, except for code.
4. Translate each sentence as one sentence with the same meaning.
5. Use the same Portuguese term for the same English term in all names and sentences.

Your final response must strictly follow this JSON template, with one entry for each name and each sentence:
{
    "N1": "Translation of name N1",
    "R1": "Translation of sentence R1",
    ...
}"""

_CLOSING = "Now follow the instructions in system message and perform the task."


def _user_prompt(names: list[str], sentences: list[str]) -> str:
    return (
        "# Names:\n"
        + "\n".join(f"N{i}: {name}" for i, name in enumerate(names, 1))
        + "\n\n# Sentences:\n"
        + "\n".join(f"R{i}: {sentence}" for i, sentence in enumerate(sentences, 1))
        + "\n\n"
        + _CLOSING
    )


def parse_translations(response: dict, n_names: int, n_sentences: int) -> dict[str, str]:
    # Um texto traduzido para cada nome e cada justificativa, e nada a mais
    names = {f"N{i}" for i in range(1, n_names + 1)}
    expected = names | {f"R{i}" for i in range(1, n_sentences + 1)}
    if not isinstance(response, dict) or set(response) != expected:
        raise InvalidLLMResponseError("a resposta não traz uma tradução para cada texto")
    for key, text in response.items():
        if not isinstance(text, str) or not text.strip():
            raise InvalidLLMResponseError(f"{key} veio sem tradução")
    return response


def translate_kc_texts(
    names: list[str], reasonings: list[str], llm: LLMClient
) -> tuple[list[str], list[str]]:
    # O português dos nomes e das justificativas, na mesma ordem, numa chamada só por exercício
    if not names and not reasonings:
        return [], []
    # Uma justificativa repetida vai uma vez só, e a tradução volta para todas as cópias
    sentences = list(dict.fromkeys(reasonings))

    def validate(response: dict) -> None:
        parse_translations(response, len(names), len(sentences))

    response = llm.generate(_SYSTEM, _user_prompt(names, sentences), validate=validate)
    translated = parse_translations(response, len(names), len(sentences))
    translated_of = {sentence: translated[f"R{i}"] for i, sentence in enumerate(sentences, 1)}
    return [translated[f"N{i}"] for i in range(1, len(names) + 1)], [
        translated_of[reasoning] for reasoning in reasonings
    ]
