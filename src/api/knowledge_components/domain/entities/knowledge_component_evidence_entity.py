# Um trecho de uma solução amostrada em que o conceito aparece, pela primeira e pela última linha.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeComponentEvidence:
    assignment_id: int
    problem_id: int
    kc_id: int  # o conceito que o trecho mostra
    position: int  # a solução amostrada em que o trecho está, pela posição dela no prompt
    first_line: int  # a primeira linha do trecho na solução, a partir de 1
    last_line: int  # a última linha do trecho, inclusive
