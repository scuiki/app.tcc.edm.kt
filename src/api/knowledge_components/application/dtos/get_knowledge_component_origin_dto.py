# A resposta de GET /knowledge-components/{kc_id}/origin, sem o nome gerado e sem o texto em inglês.

from __future__ import annotations

from pydantic import BaseModel


class KnowledgeComponentEvidenceDTO(BaseModel):
    position: int  # a solução amostrada em que o trecho está
    first_line: int  # a partir de 1
    last_line: int  # inclusive


class SampledSolutionDTO(BaseModel):
    position: int  # a ordem da solução no prompt, a partir de 1
    code: str  # com o `\r\n` e as tabulações do aluno


class ProblemOriginDTO(BaseModel):
    problem_id: int
    statement: str | None
    translated_reasonings: list[str]  # na ordem da posição, vazia no vínculo do professor
    evidence: KnowledgeComponentEvidenceDTO | None  # nulo quando o par não tem trecho
    sampled_solutions: list[SampledSolutionDTO]  # vazia se ninguém acertou o problema


class KnowledgeComponentOriginDTO(BaseModel):
    kc_id: int
    name: str
    is_generated_by_llm: bool
    problems: list[ProblemOriginDTO]  # os problemas ligados ao conceito, em ordem
