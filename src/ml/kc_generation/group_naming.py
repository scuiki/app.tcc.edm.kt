# Etapa 4 do KCGen-KT, pede ao LLM o nome de cada grupo de KCs com o prompt da Tabela 10 do paper.

from __future__ import annotations

import json

from ml.kc_generation.llm_client import InvalidLLMResponseError, LLMClient

# As palavras da Tabela 10 de Duan et al. (2026) na disposição de linhas do repositório
_SYSTEM = """You are an experienced computer science teacher and education expert. You will be provided with a list of knowledge components (KCs) that may vary in wording but sometimes refer to the same or related underlying concepts or skills.

The KCs will be given in the format: ["KC 1 name", "KC 2 name", ..., "KC k name"]

Your task is to:
1. Carefully examine all the KCs in the list to ensure none are overlooked.
2. Reason explicitly whether the KCs collectively refer to the same underlying concept or skill, or if they are related but represent distinct or complementary aspects of a broader theme.
3. Based on your reasoning:
    - If the KCs refer to the same concept or skill, select one KC from the list that best represents the group — choose the one that is most clearly worded, generalizable, and inclusive of the others.
    - If the KCs are related but too distinct to be represented by a single KC, create a concise and meaningful summary name that captures the broader theme or category shared by the KCs.

Return your output strictly in the following JSON format:
{
  "reasoning": "...",        // Exactly one sentence explaining your reasoning
  "representative kc": "..." , // Selected KC if applicable, otherwise null
  "summary name": "..." ,       // Summary name if representative KC not chosen, otherwise null
}
"""


def _user_prompt(kc_names: list[str]) -> str:
    # A lista vai no formato que o texto de sistema anuncia, como o repositório faz com json.dumps
    return (
        "The knowledge components list is: "
        + json.dumps(kc_names)
        + "\n\nNow follow the instructions in system message and perform the task."
    )


def parse_group_name(response: dict) -> str:
    # O representante ou, quando ele é nulo, o resumo, em minúsculas como o repositório
    reasoning = response.get("reasoning") if isinstance(response, dict) else None
    if not isinstance(reasoning, str) or not reasoning.strip():
        raise InvalidLLMResponseError("a resposta não trouxe a justificativa")
    representative = response.get("representative kc")
    name = representative if representative is not None else response.get("summary name")
    if not isinstance(name, str) or not name.strip():
        raise InvalidLLMResponseError("a resposta não trouxe nem o representante nem o resumo")
    return name.lower()


def name_kc_group(kc_names: list[str], llm: LLMClient) -> str:
    # Só grupos com mais de um KC chegam aqui, o de um KC só fica com o nome dele
    response = llm.generate(_SYSTEM, _user_prompt(kc_names), validate=parse_group_name)
    return parse_group_name(response)
