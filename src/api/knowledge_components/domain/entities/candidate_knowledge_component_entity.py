# Um KC que o LLM listou para um problema na extração, com a justificativa e o conceito em que caiu.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateKnowledgeComponent:
    assignment_id: int
    problem_id: int
    position: int  # a ordem do KC na resposta do LLM, a partir de 1
    name: str  # em inglês, como o LLM escreveu
    reasoning: str  # a justificativa do LLM, em inglês
    kc_id: int  # o conceito em que o KC caiu
    translated_reasoning: str | None = None  # a justificativa em português, da tradução
