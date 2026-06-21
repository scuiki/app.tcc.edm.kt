"""Dataclasses das 8 entidades de domínio (D-01), espelhando o schema 0001.

Módulo de dados puro no estilo de config.py (__future__ annotations, type hints completos):
sem I/O, sem SQL — os repositórios (repositories.py) fazem o mapeamento linha↔objeto. Os
campos são SÓ os que esta fase exercita no round-trip (D-01); kc/qmatrix/mastery_prediction
nascem mínimas e crescem por ALTER TABLE nas fases 5-6.

Convenção de id: nasce None antes do insert; o repo devolve o lastrowid e o get() o repopula.
ModelArtifact é frozen (write-once por domínio, D-05/D-06), espelhando o MappingProxyType de
config.py:35.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Turma:
    id: Optional[int]
    name: str
    created_at: str


@dataclass
class Assignment:
    id: Optional[int]
    turma_id: int
    name: str
    current_version_id: Optional[int]  # ponteiro para o ModelArtifact publicado; nasce None (D-06)
    created_at: str


@dataclass
class Submission:
    id: Optional[int]
    assignment_id: int
    code_state_id: str
    subject_id: Optional[str]
    problem_id: Optional[int]
    score: Optional[float]
    created_at: str


@dataclass
class KC:
    id: Optional[int]
    assignment_id: int
    name: str


@dataclass
class QMatrix:
    id: Optional[int]
    assignment_id: int
    kc_id: int
    problem_id: int


@dataclass(frozen=True)
class ModelArtifact:
    id: Optional[int]
    assignment_id: int
    version_number: int
    content_hash: Optional[str]  # SHA-256 dos bytes: integridade/dedup, não identidade (D-04)
    artifact_dir: str  # caminho do blob no FS; NUNCA os bytes (CLAUDE.md §Persistência)
    created_at: str


@dataclass
class MasteryPrediction:
    id: Optional[int]
    model_artifact_id: int
    subject_id: str
    kc_id: int
    mastery: Optional[float]


@dataclass
class TrainingJob:
    id: Optional[int]
    assignment_id: int
    status: str
    created_at: str
